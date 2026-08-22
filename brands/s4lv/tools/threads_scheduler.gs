// s4lv Threads scheduled poster + insight collector (Google Apps Script,
// bound to the queue spreadsheet)
//
// Ported from brands/vivant/tools/threads_scheduler.gs (2026-08-21 横展開).
// This is the Phase1-4 subset plus a READ-ONLY GitHub sync for weekly
// cloud-routine analysis. Unlike MBTICODE's full Phase5, there is NO
// pullBatchFromGitHub()/doPost() write-back here — the weekly routine only
// reads data and writes a report + push notification, it never auto-adjusts
// posting content or the queue. Add write-back later only if explicitly
// decided (see [[project_mbticode_threads_full_automation_notekaigi_0726]]
// for why MBTICODE kept a manual weekly hand-off step even after automating
// judgment: the cloud sandbox cannot push to GitHub, 403 on write).
//
// One-time setup (run these from the Apps Script editor, Run menu):
//   1. Add a tab named exactly SETUP_SHEET_NAME with:
//        A1: access_token       B1: <paste the token>
//        A2: threads_user_id    B2: <paste the numeric id>
//        A3: github_token       B3: <paste a GitHub PAT, Contents: Read and write, this repo only>
//   2. setup() - reads B1/B2, stores them in Script Properties, then clears
//      B1/B2 so the token doesn't sit visibly in the sheet.
//   2b. setupGithubToken() - same idea for B3 (see GitHub sync section below).
//   3. installTriggers() - creates a 15-min recurring postScheduled trigger
//      (2026-08-23: switched from three once-daily atHour/nearMinute triggers
//      at 07:30/12:00/21:30 — those could fire a few minutes EARLY and, being
//      single-fire, silently miss that day's post with no later trigger to
//      catch it. Actual posting times are still controlled by 投稿日時 in the
//      queue, s4lv 2026-08-21 決定の07:30/12:00/21:30 = ブロガー層の生活導線を
//      想定した1日3本のまま — only the "how often do we check" mechanism
//      changed), the daily 23:30 insight-collection / 23:35 observation-log /
//      23:40 GitHub-sync / 23:45 health-check triggers, and the weekly
//      (Mon 07:00) token refresh trigger.
//
// Sheet: a tab named exactly SHEET_NAME, row 1 = header, columns in this order:
//   投稿日時 | 本文 | リプライ1本文 | リプライ2本文 | リプライ3本文 | リプライ4本文 | 型 | FW |
//   ステータス | 投稿ID | リプライ1投稿ID | リプライ2投稿ID | リプライ3投稿ID | リプライ4投稿ID
// 投稿日時 must be an actual Date/time cell (not plain text) so comparisons work.
// 2026-08-23: extended from a single self-reply slot to up to 4 chained replies
// (連続スレッド対応). リプライ2/3/4 are optional — leave blank to post only the
// main text (+ optional リプライ1本文, as before). Each non-empty reply is
// posted as a reply to the PREVIOUS post in the chain (main post, then
// reply1, then reply2, ...), not all as replies to the main post.
//
// Insight tab: a tab named exactly INSIGHTS_SHEET_NAME, row 1 = header:
//   投稿ID | 投稿日時 | 型 | FW | Views | Likes | Replies | Reposts | Quotes | 取得日時
// One row per post, overwritten in place each day collectInsights() runs
// (a snapshot of "latest known numbers", not a full history timeline).
//
// Daily observation log: a tab named exactly OBS_SHEET_NAME, row 1 = header:
//   日付 | 集計対象投稿数 | 合計Views | 合計Likes | 合計Replies | 合計Reposts |
//   合計Quotes | エンゲージ率(%) | 返信率(%) | いいね率(%) | リポスト率(%) | 記録日時
// dailyObservationLog() re-aggregates the whole INSIGHTS_SHEET_NAME every run
// and upserts one row per calendar date (keyed by 日付).

const SHEET_NAME = "Threads投稿キュー";
const SETUP_SHEET_NAME = "設定";
const INSIGHTS_SHEET_NAME = "インサイト";
const OBS_SHEET_NAME = "日次観測ログ";
const COL = {
  DATETIME: 1, TEXT: 2,
  REPLY1: 3, REPLY2: 4, REPLY3: 5, REPLY4: 6,
  TYPE: 7, FW: 8, STATUS: 9, POST_ID: 10,
  REPLY_POST_ID1: 11, REPLY_POST_ID2: 12, REPLY_POST_ID3: 13, REPLY_POST_ID4: 14
};
// Ordered list used by postScheduled() to walk the reply chain.
const REPLY_COL_PAIRS = [
  [COL.REPLY1, COL.REPLY_POST_ID1], [COL.REPLY2, COL.REPLY_POST_ID2],
  [COL.REPLY3, COL.REPLY_POST_ID3], [COL.REPLY4, COL.REPLY_POST_ID4]
];
const ICOL = { POST_ID: 1, DATETIME: 2, TYPE: 3, FW: 4, VIEWS: 5, LIKES: 6, REPLIES: 7, REPOSTS: 8, QUOTES: 9, FETCHED_AT: 10 };
const OCOL = {
  DATE: 1, POST_COUNT: 2, VIEWS: 3, LIKES: 4, REPLIES: 5, REPOSTS: 6, QUOTES: 7,
  ENGAGEMENT_RATE: 8, REPLY_RATE: 9, LIKE_RATE: 10, REPOST_RATE: 11, RECORDED_AT: 12
};
const BASE = "https://graph.threads.net/v1.0";

// GitHub sync (2026-08-02, read-only variant of MBTICODE's relay): Apps Script
// pushes a snapshot of observation data to the repo daily, so the weekly cloud
// routine (which can read the repo via its own git clone but cannot reach
// script.google.com or push back to GitHub) has fresh data to analyze.
const GITHUB_OWNER = "t377takuwork-debug";
const GITHUB_REPO = "claude-project";
const GITHUB_BRANCH = "main";
const GITHUB_SYNC_PATH = "brands/s4lv/tools/_synced_observation_data.json";
const GITHUB_API_BASE = "https://api.github.com";

// Debug helper: lists every sheet/tab name this script actually sees, with
// its exact length (to catch stray spaces/invisible characters).
function listSheets() {
  const sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  sheets.forEach(function (s) {
    Logger.log('"' + s.getName() + '" (length=' + s.getName().length + ')');
  });
  Logger.log("Bound spreadsheet name: " + SpreadsheetApp.getActiveSpreadsheet().getName());
}

function setup() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SETUP_SHEET_NAME);
  if (!sheet) { Logger.log('ERROR: sheet "' + SETUP_SHEET_NAME + '" not found. Create it first.'); return; }
  const token = String(sheet.getRange("B1").getValue()).trim();
  const userId = String(sheet.getRange("B2").getValue()).trim();
  if (!token || !userId) { Logger.log("setup aborted: B1 (access_token) or B2 (threads_user_id) is empty"); return; }
  PropertiesService.getScriptProperties().setProperties({
    THREADS_ACCESS_TOKEN: token,
    THREADS_USER_ID: userId
  });
  sheet.getRange("B1:B2").clearContent();
  Logger.log("setup OK: saved to Script Properties, and cleared B1:B2 from the sheet");
}

// One-time: paste a GitHub Personal Access Token (Contents: read/write scope
// on this repo) into 設定 tab B3, then run this once. Needed for
// syncDataToGitHub() to call the GitHub Contents API.
function setupGithubToken() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SETUP_SHEET_NAME);
  if (!sheet) { Logger.log('ERROR: sheet "' + SETUP_SHEET_NAME + '" not found. Create it first.'); return; }
  const token = String(sheet.getRange("B3").getValue()).trim();
  if (!token) { Logger.log("setupGithubToken aborted: B3 (github_token) is empty"); return; }
  PropertiesService.getScriptProperties().setProperty("GITHUB_TOKEN", token);
  sheet.getRange("B3").clearContent();
  Logger.log("setupGithubToken OK: saved to Script Properties, and cleared B3 from the sheet");
}

function githubHeaders() {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  return { "Authorization": "token " + token, "Accept": "application/vnd.github+json" };
}

// Returns { content(base64), sha } or null if the file doesn't exist (404).
function githubGetFile(path) {
  const url = GITHUB_API_BASE + "/repos/" + GITHUB_OWNER + "/" + GITHUB_REPO + "/contents/" + path + "?ref=" + GITHUB_BRANCH;
  const resp = UrlFetchApp.fetch(url, { headers: githubHeaders(), muteHttpExceptions: true });
  if (resp.getResponseCode() === 404) return null;
  if (resp.getResponseCode() >= 300) throw new Error("GitHub GET failed: HTTP " + resp.getResponseCode() + " " + resp.getContentText());
  return JSON.parse(resp.getContentText());
}

function githubPutFile(path, contentObj, message) {
  const existing = githubGetFile(path);
  const body = {
    message: message,
    content: Utilities.base64Encode(JSON.stringify(contentObj, null, 2), Utilities.Charset.UTF_8),
    branch: GITHUB_BRANCH
  };
  if (existing) body.sha = existing.sha;
  const url = GITHUB_API_BASE + "/repos/" + GITHUB_OWNER + "/" + GITHUB_REPO + "/contents/" + path;
  const resp = UrlFetchApp.fetch(url, {
    method: "put", headers: githubHeaders(), contentType: "application/json",
    payload: JSON.stringify(body), muteHttpExceptions: true
  });
  if (resp.getResponseCode() >= 300) throw new Error("GitHub PUT failed: HTTP " + resp.getResponseCode() + " " + resp.getContentText());
  return JSON.parse(resp.getContentText());
}

// Shared payload builder: daily observation log rows + queue posts joined
// with their insight metrics, plus a per-type (型①/②/③) rollup so the
// weekly routine doesn't have to re-derive it from raw rows.
function buildObservationPayload() {
  const obsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OBS_SHEET_NAME);
  const observations = [];
  if (obsSheet) {
    const rows = obsSheet.getDataRange().getValues();
    for (let r = 1; r < rows.length; r++) {
      const row = rows[r];
      if (!row[OCOL.DATE - 1]) continue;
      observations.push({
        date: row[OCOL.DATE - 1] instanceof Date
          ? Utilities.formatDate(row[OCOL.DATE - 1], Session.getScriptTimeZone(), "yyyy-MM-dd")
          : String(row[OCOL.DATE - 1]),
        post_count: row[OCOL.POST_COUNT - 1], views: row[OCOL.VIEWS - 1], likes: row[OCOL.LIKES - 1],
        replies: row[OCOL.REPLIES - 1], reposts: row[OCOL.REPOSTS - 1], quotes: row[OCOL.QUOTES - 1],
        engagement_rate: row[OCOL.ENGAGEMENT_RATE - 1], reply_rate: row[OCOL.REPLY_RATE - 1],
        like_rate: row[OCOL.LIKE_RATE - 1], repost_rate: row[OCOL.REPOST_RATE - 1]
      });
    }
  }

  const queueSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const insightSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INSIGHTS_SHEET_NAME);
  const insightByPostId = {};
  if (insightSheet) {
    const irows = insightSheet.getDataRange().getValues();
    for (let r = 1; r < irows.length; r++) {
      const row = irows[r];
      if (!row[ICOL.POST_ID - 1]) continue;
      insightByPostId[row[ICOL.POST_ID - 1]] = {
        views: row[ICOL.VIEWS - 1], likes: row[ICOL.LIKES - 1], replies: row[ICOL.REPLIES - 1],
        reposts: row[ICOL.REPOSTS - 1], quotes: row[ICOL.QUOTES - 1]
      };
    }
  }
  const posts = [];
  if (queueSheet) {
    const qrows = queueSheet.getDataRange().getValues();
    for (let r = 1; r < qrows.length; r++) {
      const row = qrows[r];
      const postId = row[COL.POST_ID - 1];
      if (row[COL.STATUS - 1] !== "投稿済み" || !postId) continue;
      const m = insightByPostId[postId] || {};
      posts.push({
        post_id: postId,
        datetime: row[COL.DATETIME - 1] instanceof Date
          ? Utilities.formatDate(row[COL.DATETIME - 1], Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm")
          : String(row[COL.DATETIME - 1]),
        body: row[COL.TEXT - 1], type: row[COL.TYPE - 1], fw: row[COL.FW - 1],
        views: m.views || 0, likes: m.likes || 0, replies: m.replies || 0,
        reposts: m.reposts || 0, quotes: m.quotes || 0
      });
    }
  }

  return { generated_at: new Date().toISOString(), observations: observations, posts: posts };
}

// Daily (23:40, after dailyObservationLog): mirrors the observation payload
// into the GitHub repo so the weekly cloud routine (which cannot reach
// script.google.com) can read fresh data via its own repo checkout.
// READ-ONLY on the routine's side — nothing pulls data back from GitHub here.
function syncDataToGitHub() {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!token) { Logger.log("ERROR: GITHUB_TOKEN not set. Run setupGithubToken() first."); return; }
  try {
    githubPutFile(GITHUB_SYNC_PATH, buildObservationPayload(),
      "Auto-sync s4lv Threads observation data (" + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd") + ")");
    Logger.log("syncDataToGitHub: OK");
  } catch (e) {
    Logger.log("syncDataToGitHub: ERROR " + e.message);
  }
}

function installTriggers() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  // 2026-08-23: switched postScheduled from three single-fire-per-day
  // atHour/nearMinute triggers (07:30/12:00/21:30) to a 15-min recurring
  // trigger. Root cause of the switch: nearMinute() can fire a few minutes
  // EARLY as well as late (observed twice: the 07:30 trigger actually fired
  // at 7:26:37 on both 2026-08-22 and 2026-08-23). Because each of the three
  // triggers only fires once per day, an early fire meant postScheduled() saw
  // scheduledAt(07:30) > now(7:26) and skipped the row with nothing left to
  // catch it that day — the post silently didn't go out until the same
  // trigger fired again ~24h later. Polling every 15 min removes this failure
  // mode: whichever run first sees scheduledAt <= now processes the row,
  // at most ~15 min after its scheduled time, regardless of which exact
  // minute a given run lands on. 投稿頻度・時刻（07:30/12:00/21:30）自体は
  // posts_threads.txt側の投稿日時で制御するため変更なし — ここが変わるのは
  // 「いつ確認しにいくか」だけ。
  ScriptApp.newTrigger("postScheduled").timeBased().everyMinutes(15).create();
  ScriptApp.newTrigger("collectInsights").timeBased().everyDays(1).atHour(23).nearMinute(30).create();
  ScriptApp.newTrigger("dailyObservationLog").timeBased().everyDays(1).atHour(23).nearMinute(35).create();
  ScriptApp.newTrigger("syncDataToGitHub").timeBased().everyDays(1).atHour(23).nearMinute(40).create();
  ScriptApp.newTrigger("checkHealth").timeBased().everyDays(1).atHour(23).nearMinute(45).create();
  ScriptApp.newTrigger("refreshToken").timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  Logger.log("triggers installed: postScheduled every 15min, collectInsights 23:30 daily, dailyObservationLog 23:35 daily, syncDataToGitHub 23:40 daily, checkHealth 23:45 daily, refreshToken Mon 07:00");
}

// Daily (Phase2 equivalent): re-aggregates INSIGHTS_SHEET_NAME into
// one summary row per calendar date in OBS_SHEET_NAME. Collection only — does
// not change posting content or schedule. Run after collectInsights so the
// day's numbers are current when this runs.
function dailyObservationLog() {
  const insightSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INSIGHTS_SHEET_NAME);
  const obsSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OBS_SHEET_NAME);
  if (!insightSheet) { Logger.log('ERROR: sheet "' + INSIGHTS_SHEET_NAME + '" not found.'); return; }
  if (!obsSheet) { Logger.log('ERROR: sheet "' + OBS_SHEET_NAME + '" not found. Create it first.'); return; }

  const data = insightSheet.getDataRange().getValues();
  let views = 0, likes = 0, replies = 0, reposts = 0, quotes = 0, count = 0;
  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    if (!row[ICOL.POST_ID - 1]) continue;
    views += Number(row[ICOL.VIEWS - 1]) || 0;
    likes += Number(row[ICOL.LIKES - 1]) || 0;
    replies += Number(row[ICOL.REPLIES - 1]) || 0;
    reposts += Number(row[ICOL.REPOSTS - 1]) || 0;
    quotes += Number(row[ICOL.QUOTES - 1]) || 0;
    count++;
  }

  const engRate = views > 0 ? (likes + replies + reposts + quotes) / views * 100 : 0;
  const replyRate = views > 0 ? replies / views * 100 : 0;
  const likeRate = views > 0 ? likes / views * 100 : 0;
  const repostRate = views > 0 ? reposts / views * 100 : 0;

  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
  const obsData = obsSheet.getDataRange().getValues();
  let targetRow = null;
  for (let r = 1; r < obsData.length; r++) {
    const cell = obsData[r][OCOL.DATE - 1];
    const cellDate = cell instanceof Date ? Utilities.formatDate(cell, Session.getScriptTimeZone(), "yyyy-MM-dd") : String(cell);
    if (cellDate === today) { targetRow = r + 1; break; }
  }
  if (!targetRow) targetRow = obsSheet.getLastRow() + 1;

  obsSheet.getRange(targetRow, OCOL.DATE).setValue(today);
  obsSheet.getRange(targetRow, OCOL.POST_COUNT).setValue(count);
  obsSheet.getRange(targetRow, OCOL.VIEWS).setValue(views);
  obsSheet.getRange(targetRow, OCOL.LIKES).setValue(likes);
  obsSheet.getRange(targetRow, OCOL.REPLIES).setValue(replies);
  obsSheet.getRange(targetRow, OCOL.REPOSTS).setValue(reposts);
  obsSheet.getRange(targetRow, OCOL.QUOTES).setValue(quotes);
  obsSheet.getRange(targetRow, OCOL.ENGAGEMENT_RATE).setValue(Math.round(engRate * 1000) / 1000);
  obsSheet.getRange(targetRow, OCOL.REPLY_RATE).setValue(Math.round(replyRate * 1000) / 1000);
  obsSheet.getRange(targetRow, OCOL.LIKE_RATE).setValue(Math.round(likeRate * 1000) / 1000);
  obsSheet.getRange(targetRow, OCOL.REPOST_RATE).setValue(Math.round(repostRate * 1000) / 1000);
  obsSheet.getRange(targetRow, OCOL.RECORDED_AT).setValue(new Date());

  Logger.log("dailyObservationLog: " + count + " posts, engRate=" + engRate.toFixed(3) + "%");
}

// Daily: verifies the whole pipeline is actually working, and emails the
// script owner ONLY when something looks wrong (silence = healthy). Checks:
//   - token/user id still present in Script Properties
//   - all expected triggers still installed
//   - no queue rows sitting unprocessed more than 2h past their scheduled time
//   - no queue rows with ステータス = エラー
// Apps Script also auto-emails the owner if any trigger function throws an
// uncaught exception, which backstops the case where checkHealth() itself fails.
function checkHealth() {
  const problems = [];
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty("THREADS_ACCESS_TOKEN") || !props.getProperty("THREADS_USER_ID")) {
    problems.push("トークンまたはユーザーIDがScript Propertiesに存在しません（setup()を再実行してください）");
  }
  if (!props.getProperty("GITHUB_TOKEN")) {
    problems.push("GITHUB_TOKENがScript Propertiesに存在しません（setupGithubToken()を再実行してください）");
  }

  const expectedTriggers = ["postScheduled", "collectInsights", "dailyObservationLog", "syncDataToGitHub", "checkHealth", "refreshToken"];
  const installed = ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); });
  expectedTriggers.forEach(function (fn) {
    if (installed.indexOf(fn) === -1) problems.push("トリガー未設定: " + fn + "（installTriggers()を再実行してください）");
  });

  if (!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OBS_SHEET_NAME)) {
    problems.push('シート "' + OBS_SHEET_NAME + '" が見つかりません（dailyObservationLog用・作成してください）');
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    problems.push('シート "' + SHEET_NAME + '" が見つかりません');
  } else {
    const data = sheet.getDataRange().getValues();
    const now = new Date();
    const graceMs = 2 * 60 * 60 * 1000; // 2 hours
    let stuck = 0, errors = 0;
    for (let r = 1; r < data.length; r++) {
      const row = data[r];
      const scheduledAt = row[COL.DATETIME - 1];
      const status = row[COL.STATUS - 1];
      if (status === "エラー") errors++;
      if (!(scheduledAt instanceof Date)) continue;
      if (status !== "投稿済み" && status !== "エラー" && (now - scheduledAt) > graceMs) stuck++;
    }
    if (stuck > 0) problems.push("投稿予定時刻を2時間以上過ぎても未処理の行が" + stuck + "件あります");
    if (errors > 0) problems.push("ステータスが「エラー」の行が" + errors + "件あります（投稿ID列にエラー内容が入っています）");
  }

  if (problems.length > 0) {
    const body = problems.join("\n");
    MailApp.sendEmail(Session.getEffectiveUser().getEmail(), "[s4lv Threads] 監視アラート", body);
    Logger.log("checkHealth: problem(s) found, email sent:\n" + body);
  } else {
    Logger.log("checkHealth: OK, no problems found");
  }
}

// Fires from the time-based triggers. Processes every row scheduled at or
// before "now" that isn't already 投稿済み/エラー, so a delayed trigger
// (Apps Script can fire up to ~15min late) still catches up correctly.
function postScheduled() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  const userId = props.getProperty("THREADS_USER_ID");
  if (!token || !userId) { Logger.log("ERROR: setup() has not been run yet"); return; }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const now = new Date();

  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    const scheduledAt = row[COL.DATETIME - 1];
    const status = row[COL.STATUS - 1];
    if (status === "投稿済み" || status === "エラー") continue;
    if (!(scheduledAt instanceof Date)) continue;
    if (scheduledAt > now) continue;

    try {
      const mainId = publishText(token, userId, row[COL.TEXT - 1], null);
      sheet.getRange(r + 1, COL.POST_ID).setValue(mainId);

      // Chain: reply1 replies to the main post, reply2 replies to reply1's
      // post, etc. Stops at the first blank reply slot (blank slots after a
      // filled one are treated as "thread ends here", not skipped-and-resumed).
      let previousId = mainId;
      for (let i = 0; i < REPLY_COL_PAIRS.length; i++) {
        const textCol = REPLY_COL_PAIRS[i][0];
        const idCol = REPLY_COL_PAIRS[i][1];
        const replyText = row[textCol - 1];
        if (!replyText) break;
        const replyId = publishText(token, userId, replyText, previousId);
        sheet.getRange(r + 1, idCol).setValue(replyId);
        previousId = replyId;
      }
      sheet.getRange(r + 1, COL.STATUS).setValue("投稿済み");
    } catch (e) {
      sheet.getRange(r + 1, COL.STATUS).setValue("エラー");
      sheet.getRange(r + 1, COL.POST_ID).setValue(String(e.message).slice(0, 200));
    }
  }
}

function publishText(token, userId, text, replyToId) {
  const createPayload = { media_type: "TEXT", text: text, access_token: token };
  if (replyToId) createPayload.reply_to_id = replyToId;
  const creationId = callThreads(userId + "/threads", createPayload);
  Utilities.sleep(2000); // give the container a moment to become publishable
  return callThreads(userId + "/threads_publish", { creation_id: creationId, access_token: token });
}

function callThreads(path, payload) {
  const resp = UrlFetchApp.fetch(BASE + "/" + path, {
    method: "post",
    payload: payload,
    muteHttpExceptions: true
  });
  const body = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 300) {
    throw new Error("Threads API error: " + (body.error ? body.error.message : resp.getContentText()));
  }
  return body.id;
}

// Daily: pulls insights for every 投稿済み row in SHEET_NAME and upserts a
// snapshot row (keyed by 投稿ID) into INSIGHTS_SHEET_NAME. Overwrites each
// day rather than appending a new row, so the sheet always shows "latest
// known numbers" per post, not a full growth timeline.
function collectInsights() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  if (!token) { Logger.log("ERROR: setup() has not been run yet"); return; }

  const queueSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const insightSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INSIGHTS_SHEET_NAME);
  if (!insightSheet) { Logger.log('ERROR: sheet "' + INSIGHTS_SHEET_NAME + '" not found. Create it first.'); return; }

  const queueData = queueSheet.getDataRange().getValues();
  const insightData = insightSheet.getDataRange().getValues();

  // Build a lookup of 投稿ID -> row number (1-indexed sheet row) already in the insight tab
  const existingRow = {};
  for (let i = 1; i < insightData.length; i++) {
    const id = insightData[i][ICOL.POST_ID - 1];
    if (id) existingRow[id] = i + 1;
  }

  let processed = 0;
  for (let r = 1; r < queueData.length; r++) {
    const row = queueData[r];
    if (row[COL.STATUS - 1] !== "投稿済み") continue;
    const postId = row[COL.POST_ID - 1];
    if (!postId) continue;

    let metrics;
    try {
      metrics = fetchInsights(postId, token);
    } catch (e) {
      Logger.log("insight fetch failed for " + postId + ": " + e.message);
      continue;
    }

    // Threads' replies metric counts every reply attached to the post,
    // including any reply from our own account (the automated self-reply
    // used to seed engagement, or a manual follow-up reply). Pull the actual
    // reply list and exclude every entry Threads itself flags as our own via
    // is_reply_owned_by_me, instead of guessing an offset.
    let replies;
    try {
      replies = fetchExternalReplyCount(postId, token);
    } catch (e) {
      Logger.log("reply list fetch failed for " + postId + ": " + e.message + " -- falling back to raw metric");
      replies = metrics.replies || 0;
    }

    const targetRow = existingRow[postId] || (insightSheet.getLastRow() + 1);
    insightSheet.getRange(targetRow, ICOL.POST_ID).setValue(postId);
    insightSheet.getRange(targetRow, ICOL.DATETIME).setValue(row[COL.DATETIME - 1]);
    insightSheet.getRange(targetRow, ICOL.TYPE).setValue(row[COL.TYPE - 1]);
    insightSheet.getRange(targetRow, ICOL.FW).setValue(row[COL.FW - 1]);
    insightSheet.getRange(targetRow, ICOL.VIEWS).setValue(metrics.views || 0);
    insightSheet.getRange(targetRow, ICOL.LIKES).setValue(metrics.likes || 0);
    insightSheet.getRange(targetRow, ICOL.REPLIES).setValue(replies);
    insightSheet.getRange(targetRow, ICOL.REPOSTS).setValue(metrics.reposts || 0);
    insightSheet.getRange(targetRow, ICOL.QUOTES).setValue(metrics.quotes || 0);
    insightSheet.getRange(targetRow, ICOL.FETCHED_AT).setValue(new Date());
    existingRow[postId] = targetRow;
    processed++;
  }
  Logger.log("collectInsights done: " + processed + " post(s) updated");
}

// Returns the number of replies to mediaId that were NOT posted by our own
// account, using Threads' own is_reply_owned_by_me flag on each reply so we
// never rely on a guessed offset (see collectInsights above).
function fetchExternalReplyCount(mediaId, token) {
  const uri = BASE + "/" + mediaId + "/replies?fields=is_reply_owned_by_me&access_token=" + encodeURIComponent(token);
  const resp = UrlFetchApp.fetch(uri, { muteHttpExceptions: true });
  const body = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 300) {
    throw new Error("Threads API error: " + (body.error ? body.error.message : resp.getContentText()));
  }
  const list = body.data || [];
  return list.filter(function (r) { return !r.is_reply_owned_by_me; }).length;
}

function fetchInsights(mediaId, token) {
  const uri = BASE + "/" + mediaId + "/insights?metric=views,likes,replies,reposts,quotes&access_token=" + encodeURIComponent(token);
  const resp = UrlFetchApp.fetch(uri, { muteHttpExceptions: true });
  const body = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 300) {
    throw new Error("insights API error: " + (body.error ? body.error.message : resp.getContentText()));
  }
  const out = {};
  (body.data || []).forEach(function (m) {
    // Threads insights returns either total_value.value or a values[] series depending on metric
    if (m.total_value) out[m.name] = m.total_value.value;
    else if (m.values && m.values.length) out[m.name] = m.values[m.values.length - 1].value;
  });
  return out;
}

// Weekly refresh, mirrors tools/threads_connect_test.ps1 -Step refresh.
// The new token is written straight to Script Properties, never logged.
// NOTE (lesson from MBTICODE, 2026-07-26): do NOT also run a local scheduled-task
// refresh in parallel with this trigger. Running both independently caused the
// two token copies to drift out of sync and broke scheduled posting. This
// weekly Apps Script trigger should be the ONLY place the token gets refreshed.
function refreshToken() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  if (!token) { Logger.log("ERROR: setup() has not been run yet"); return; }
  const resp = UrlFetchApp.fetch(
    BASE + "/refresh_access_token?grant_type=th_refresh_token&access_token=" + encodeURIComponent(token),
    { muteHttpExceptions: true }
  );
  const body = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 300) {
    Logger.log("refresh failed: HTTP " + resp.getResponseCode());
    return;
  }
  props.setProperty("THREADS_ACCESS_TOKEN", body.access_token);
  Logger.log("refreshed OK, expires_in=" + body.expires_in + " seconds");
}
