// MBTICODE Threads scheduled poster + insight collector (Google Apps Script,
// bound to the queue spreadsheet)
//
// One-time setup (run these from the Apps Script editor, Run menu):
//   1. Add a tab named exactly SETUP_SHEET_NAME with:
//        A1: access_token       B1: <paste the token>
//        A2: threads_user_id    B2: <paste the numeric id>
//        A3: github_token       B3: <paste a GitHub PAT with Contents read/write on this repo>
//   2. setup() - reads B1/B2, stores them in Script Properties, then clears
//      B1/B2 so the token doesn't sit visibly in the sheet. No dialogs involved,
//      so it works regardless of which tab/window is focused when you click Run.
//   2b. setupGithubToken() - same idea for B3 (see GitHub relay section below).
//   3. installTriggers() - creates the 08:00 / 12:00 / 16:00 / 19:00 / 22:00 posting
//      triggers (2026-08-16notekaigi: increased from 3/day to 5/day),
//      the daily 23:30 insight-collection / 23:35 observation-log / 23:40
//      GitHub-sync triggers, the every-10-minutes external-reply-detection /
//      reply-candidate-sync / delayed-URL-reply-posting triggers (see
//      postDelayedUrlReplies below), the hourly generated-reply-pull trigger
//      (2026-08-16notekaigi Phase5 timing revision: detection polls every
//      10min but the cloud drafting routine can only run hourly at minimum --
//      see detectExternalReplies below and sns_post_cheatsheet.md「外部リプライ
//      自動応答」for the full reasoning), the weekly (Mon 07:00) token refresh
//      trigger, and the weekly (Sun 21:00) GitHub batch-pull trigger.
//      (2026-09-29: the 10:00/14:00/18:00/21:00/00:00 early-performance-check
//      trigger and checkEarlyPerformance() itself were removed -- the
//      "反響を見てから動く" reactive URL-CTA feature is discontinued in favor of
//      always seeding proven-strong リスト型 posts with a URL reply at write
//      time, see 「型ローテーション比率」in sns_post_cheatsheet.md.)
//
// Sheet: a tab named exactly SHEET_NAME, row 1 = header, columns in this order:
//   投稿日時 | 本文 | リプライ本文 | 型 | FW | ステータス | 投稿ID | リプライ投稿ID |
//   リプライ投稿予定日時(未使用の旧列) | URL自己リプライ本文 | URL自己リプライ投稿ID
// 投稿日時 must be an actual Date/time cell (not plain text) so comparisons work.
// 型・FW are free-text tags (e.g. "型B", "MBTI(ESFJ)") copied from posts_threads.txt
// when the row is created; used later to correlate insights with content category.
// ステータス starts empty/"未投稿"; this script writes "投稿済み" or "エラー".
// リプライ本文 containing a URL is NOT posted immediately alongside the main
// post -- postScheduled() skips it and leaves リプライ投稿ID empty, and
// postDelayedUrlReplies() (2026-09-19 user request) posts it once the main
// post is at least URL_REPLY_DELAY_MS old (poll every 10min, act once past
// the threshold). Reply text with no URL (続き型 etc.) still posts
// immediately, as before. The same function also handles 列J（URL自己リプライ
// 本文, 2026-09-29追加）on the same delay/polling basis, see below.
//
// Insight tab: a tab named exactly INSIGHTS_SHEET_NAME, row 1 = header:
//   投稿ID | 投稿日時 | 型 | FW | Views | Likes | Replies | Reposts | Quotes | 取得日時
// One row per post, overwritten in place each day collectInsights() runs
// (a snapshot of "latest known numbers", not a full history timeline).
//
// External-reply auto-response tab (2026-08-16notekaigi Phase5): a tab named
// exactly REPLY_QUEUE_SHEET_NAME, row 1 = header:
//   リプライID | 元投稿ID | 元投稿本文 | 投稿者 | リプライ本文 | 受信日時 |
//   ステータス | 生成した返信文 | 返信投稿ID
// detectExternalReplies() appends rows (ステータス=未処理) for every new
// external reply found. syncReplyCandidatesToGitHub() mirrors 未処理 rows to
// GitHub for the scheduled reply-drafting cloud routine to read (fully
// automatic, no human review step -- see sns_post_cheatsheet.md「外部リプライ
// 自動応答」). pullGeneratedRepliesFromGitHub() posts the routine's drafted
// text and flips ステータス to 投稿済み/エラー. Create this tab manually
// before running installTriggers().
//
// Daily observation log (2026-07-26notekaigi Phase2): a tab named exactly
// OBS_SHEET_NAME, row 1 = header:
//   日付 | 集計対象投稿数 | 合計Views | 合計Likes | 合計Replies | 合計Reposts |
//   合計Quotes | エンゲージ率(%) | 返信率(%) | いいね率(%) | リポスト率(%) | 記録日時
// dailyObservationLog() re-aggregates the whole INSIGHTS_SHEET_NAME every run
// and upserts one row per calendar date (keyed by 日付), so this is a rolling
// "cumulative snapshot as of that day" series, not a per-day delta. This is
// collection only — no judgment/adjustment happens here (that stays weekly,
// Phase3, with a human-agreed variable list and the qa_post.py content-policy
// gate in front of anything auto-posted).

const SHEET_NAME = "Threads投稿キュー";
const SETUP_SHEET_NAME = "設定";
const INSIGHTS_SHEET_NAME = "インサイト";
const OBS_SHEET_NAME = "日次観測ログ";
const COL = {
  DATETIME: 1, TEXT: 2, REPLY: 3, TYPE: 4, FW: 5, STATUS: 6, POST_ID: 7, REPLY_POST_ID: 8,
  // 列I（"リプライ投稿予定日時"）はシート上に見出しだけ残る未使用の旧列（このスクリプトはどこも読み書きしない）。
  // 列J/K（2026-09-29追加）: リスト型・続き型など、列C（1本目の自己リプライ）が既に
  // 本文の続き等で使われている投稿向けの、2本目の自己リプライ（URL誘導専用）。
  // 「反響が伸びやすいと実績のあるリスト型には、判定を待たず最初からURL誘導を仕込む」方針
  // （旧checkEarlyPerformanceの「反響を見てから動く」方式は2026-09-29に廃止済み。こちらは
  // その反射的な判定を待たない、計画的な仕込み）。
  URL_REPLY: 10, URL_REPLY_ID: 11
};
const ICOL = { POST_ID: 1, DATETIME: 2, TYPE: 3, FW: 4, VIEWS: 5, LIKES: 6, REPLIES: 7, REPOSTS: 8, QUOTES: 9, FETCHED_AT: 10 };
const OCOL = {
  DATE: 1, POST_COUNT: 2, VIEWS: 3, LIKES: 4, REPLIES: 5, REPOSTS: 6, QUOTES: 7,
  ENGAGEMENT_RATE: 8, REPLY_RATE: 9, LIKE_RATE: 10, REPOST_RATE: 11, RECORDED_AT: 12
};
const REPLY_QUEUE_SHEET_NAME = "外部リプライキュー";
const RCOL = {
  REPLY_ID: 1, POST_ID: 2, POST_BODY: 3, AUTHOR: 4, REPLY_TEXT: 5,
  RECEIVED_AT: 6, STATUS: 7, GENERATED_REPLY: 8, REPLY_POST_ID: 9
};
const BASE = "https://graph.threads.net/v1.0";

// 2026-09-21: detectExternalRepliesが「投稿済み全件」を10分おきにスキャンする作りだったため、
// 投稿が146件に積み上がった時点でurlfetchの1日上限(20,000回)を超えてエラーになった
// （146件×144回/日=約21,000回。投稿頻度ではなく累積投稿数と10分間隔の掛け算が原因）。
// 投稿から日数が経つほど新規の外部リプライは実質発生しないため、直近分だけに絞る
// （3日なら1日5本×3日=15件×144回/日=約2,160回で十分な余裕がある）。
const EXTERNAL_REPLY_LOOKBACK_DAYS = 3;

// GitHub relay (2026-07-26notekaigi Phase3 redesign): the cloud routine's
// sandbox cannot reach script.google.com (egress policy blocks it, confirmed
// by testing), so instead of the cloud agent calling this Web App directly,
// data flows one-way through the GitHub repo, which the cloud agent CAN
// reach (it clones the repo already):
//   syncDataToGitHub()   : Apps Script -> GitHub. Daily. Writes the same
//                          payload as doGet(?action=data) to GITHUB_SYNC_PATH.
//   pullBatchFromGitHub(): GitHub -> Apps Script. Weekly. Reads rows the
//                          cloud agent committed to GITHUB_BATCH_PATH,
//                          appends them to the queue, then deletes the file
//                          (consumed-once semantics, so a stale batch never
//                          gets re-applied the following week).
const GITHUB_OWNER = "t377takuwork-debug";
const GITHUB_REPO = "claude-project";
const GITHUB_BRANCH = "main";
const GITHUB_SYNC_PATH = "brands/mbticode/tools/_synced_observation_data.json";
const GITHUB_BATCH_PATH = "brands/mbticode/tools/_pending_batch.json";
const GITHUB_API_BASE = "https://api.github.com";

// 外部リプライ自動応答（2026-08-16notekaigi Phase5）: 同じGitHub中継パターンを
// 「他者からの新規リプライ」向けに複製したもの。
//   detectExternalReplies()      : Threads -> REPLY_QUEUE_SHEET_NAME. Daily.
//   syncReplyCandidatesToGitHub(): REPLY_QUEUE_SHEET_NAME -> GitHub. Daily,
//                                  未処理行のみ。スケジュール実行される返信文
//                                  生成ルーティン（sns_post_cheatsheet.md
//                                  「外部リプライ自動応答」参照）がこれを読む。
//   pullGeneratedRepliesFromGitHub(): GitHub -> Threads投稿 + シート更新。Daily。
const GITHUB_REPLY_CANDIDATES_PATH = "brands/mbticode/tools/_reply_candidates.json";
const GITHUB_PENDING_REPLIES_PATH = "brands/mbticode/tools/_pending_reply_posts.json";

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

// One-time (2026-07-26notekaigi Phase3): generates a random secret used to
// authenticate the Web App endpoints below (doGet/doPost). Deploying as a Web
// App requires "Anyone" access at the Google layer, so this secret is the
// ONLY thing actually protecting these endpoints — never skip checking it.
// Run once, copy the secret from the execution log, and give it to whatever
// external caller (e.g. a scheduled cloud agent) needs to hit this Web App.
function setupWebhookSecret() {
  const secret = Utilities.getUuid();
  PropertiesService.getScriptProperties().setProperty("WEBHOOK_SECRET", secret);
  Logger.log("Webhook secret generated (copy this now, it will not be shown again by this function): " + secret);
}

// One-time: paste a GitHub Personal Access Token (Contents: read/write scope
// on this repo) into 設定 tab B3, then run this once. Needed for
// syncDataToGitHub()/pullBatchFromGitHub() to call the GitHub Contents API.
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

function githubDeleteFile(path, sha, message) {
  const url = GITHUB_API_BASE + "/repos/" + GITHUB_OWNER + "/" + GITHUB_REPO + "/contents/" + path;
  const resp = UrlFetchApp.fetch(url, {
    method: "delete", headers: githubHeaders(), contentType: "application/json",
    payload: JSON.stringify({ message: message, sha: sha, branch: GITHUB_BRANCH }), muteHttpExceptions: true
  });
  if (resp.getResponseCode() >= 300) throw new Error("GitHub DELETE failed: HTTP " + resp.getResponseCode() + " " + resp.getContentText());
}

// Shared by doGet(?action=data) and syncDataToGitHub() so both expose the
// exact same payload shape.
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

// Daily (after dailyObservationLog, e.g. 23:40): mirrors the observation
// payload into the GitHub repo so the cloud routine (which cannot reach
// script.google.com) can read fresh data via its own repo checkout.
function syncDataToGitHub() {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!token) { Logger.log("ERROR: GITHUB_TOKEN not set. Run setupGithubToken() first."); return; }
  try {
    githubPutFile(GITHUB_SYNC_PATH, buildObservationPayload(),
      "Auto-sync Threads observation data (" + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd") + ")");
    Logger.log("syncDataToGitHub: OK");
  } catch (e) {
    Logger.log("syncDataToGitHub: ERROR " + e.message);
  }
}

// Weekly (e.g. Sunday 21:00 JST, after the cloud routine's 18:00 JST run):
// reads GITHUB_BATCH_PATH (rows the cloud agent committed after passing the
// qa_post.py gate), appends them to the queue with the same safety guards as
// doPost, then deletes the file so it's never re-applied.
function pullBatchFromGitHub() {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!token) { Logger.log("ERROR: GITHUB_TOKEN not set. Run setupGithubToken() first."); return; }

  let file;
  try {
    file = githubGetFile(GITHUB_BATCH_PATH);
  } catch (e) {
    Logger.log("pullBatchFromGitHub: ERROR fetching file: " + e.message);
    return;
  }
  if (!file) { Logger.log("pullBatchFromGitHub: no pending batch file found, nothing to do"); return; }

  let payload;
  try {
    const jsonStr = Utilities.newBlob(Utilities.base64Decode(file.content.replace(/\n/g, ""))).getDataAsString("UTF-8");
    payload = JSON.parse(jsonStr);
  } catch (e) {
    Logger.log("pullBatchFromGitHub: ERROR parsing batch JSON: " + e.message);
    return;
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) { Logger.log('ERROR: sheet "' + SHEET_NAME + '" not found'); return; }
  const existing = sheet.getDataRange().getValues();
  const existingSerials = {};
  for (let r = 1; r < existing.length; r++) {
    const v = existing[r][COL.DATETIME - 1];
    if (v instanceof Date) existingSerials[Math.round((v - new Date(1899, 11, 30)) / 86400000 * 1e6) / 1e6] = true;
  }

  const now = new Date();
  let added = 0, skippedPast = 0, skippedDupe = 0;
  (payload.rows || []).forEach(function (row) {
    const dt = new Date(String(row.datetime).replace(" ", "T") + ":00");
    if (isNaN(dt.getTime()) || dt < now) { skippedPast++; return; }
    const serial = Math.round((dt - new Date(1899, 11, 30)) / 86400000 * 1e6) / 1e6;
    if (existingSerials[serial]) { skippedDupe++; return; }
    sheet.appendRow([dt, row.body || "", row.reply || "", row.type || "", row.fw || "", "", "", ""]);
    existingSerials[serial] = true;
    added++;
  });

  try {
    githubDeleteFile(GITHUB_BATCH_PATH, file.sha,
      "Consume pending Threads batch (" + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd") + ")");
  } catch (e) {
    Logger.log("pullBatchFromGitHub: WARNING failed to delete consumed file: " + e.message);
  }
  Logger.log("pullBatchFromGitHub: added=" + added + " skippedPast=" + skippedPast + " skippedDupe=" + skippedDupe);
}

function checkSecret(param) {
  const expected = PropertiesService.getScriptProperties().getProperty("WEBHOOK_SECRET");
  return expected && param === expected;
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Web App GET endpoint (2026-07-26notekaigi Phase3, read side).
// ?secret=...&action=data
// Returns daily observation log rows + queue posts joined with their insight
// metrics, so an external caller can do the weekly bounded-variable analysis
// without needing direct Sheets API / service-account credentials.
function doGet(e) {
  const params = e && e.parameter ? e.parameter : {};
  if (!checkSecret(params.secret)) return jsonResponse({ error: "invalid secret" });

  if (params.action === "data") {
    return jsonResponse(buildObservationPayload());
  }

  return jsonResponse({ error: "unknown action" });
}

// Web App POST endpoint (2026-07-26notekaigi Phase3, write side).
// Body (JSON): { "secret": "...", "rows": [{datetime, body, reply, type, fw}, ...], "allow_past": false }
// datetime must be "YYYY-MM-DD HH:MM". Mirrors push_threads_queue.py's safety
// behavior: rows in the past are skipped unless allow_past is true, and rows
// whose datetime already exists in the queue are skipped (duplicate guard).
// This does NOT run qa_post.py itself — the caller must have already done
// that content-policy/style gate before calling this endpoint.
function doPost(e) {
  let payload;
  try {
    payload = JSON.parse(e.postData.contents);
  } catch (err) {
    return jsonResponse({ error: "invalid JSON body" });
  }
  if (!checkSecret(payload.secret)) return jsonResponse({ error: "invalid secret" });

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) return jsonResponse({ error: 'sheet "' + SHEET_NAME + '" not found' });

  const existing = sheet.getDataRange().getValues();
  const existingSerials = {};
  for (let r = 1; r < existing.length; r++) {
    const v = existing[r][COL.DATETIME - 1];
    if (v instanceof Date) existingSerials[Math.round((v - new Date(1899, 11, 30)) / 86400000 * 1e6) / 1e6] = true;
  }

  const now = new Date();
  const added = [], skippedPast = [], skippedDupe = [];
  (payload.rows || []).forEach(function (row) {
    const dt = new Date(row.datetime.replace(" ", "T") + ":00");
    if (isNaN(dt.getTime())) { skippedPast.push(row); return; }
    if (dt < now && !payload.allow_past) { skippedPast.push(row); return; }
    const serial = Math.round((dt - new Date(1899, 11, 30)) / 86400000 * 1e6) / 1e6;
    if (existingSerials[serial]) { skippedDupe.push(row); return; }
    sheet.appendRow([dt, row.body || "", row.reply || "", row.type || "", row.fw || "", "", "", ""]);
    existingSerials[serial] = true;
    added.push(row);
  });

  return jsonResponse({
    added_count: added.length, skipped_past_count: skippedPast.length, skipped_dupe_count: skippedDupe.length
  });
}

function installTriggers() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  // 2026-08-16notekaigi: 1日3本(8/12/22)から1日5本(8/12/16/19/22)へ増量。試験期間8/17〜8/23。
  [8, 12, 16, 19, 22].forEach(function (hour) {
    ScriptApp.newTrigger("postScheduled").timeBased().everyDays(1).atHour(hour).nearMinute(0).create();
  });
  ScriptApp.newTrigger("collectInsights").timeBased().everyDays(1).atHour(23).nearMinute(30).create();
  // 2026-08-16notekaigi Phase5改訂: 外部リプライは10分間隔で検知・同期し、
  // 生成ルーティン（クラウド側、cron最小間隔=1時間の制約）と合わせて
  // 最短ケースで1時間以内の応答を狙う（詳細はsns_post_cheatsheet.md「外部リプライ自動応答」参照）
  ScriptApp.newTrigger("detectExternalReplies").timeBased().everyMinutes(10).create();
  ScriptApp.newTrigger("syncReplyCandidatesToGitHub").timeBased().everyMinutes(10).create();
  ScriptApp.newTrigger("pullGeneratedRepliesFromGitHub").timeBased().everyHours(1).create();
  // 2026-09-19ユーザー要望: URLを含む自己リプライは本編投稿の2時間後に送る
  // （10分間隔ポーリング方式。postDelayedUrlReplies参照。2026-09-29からリスト型向けの
  // 2本目の自己リプライ＝列J/Kもこのトリガーに相乗りする）
  ScriptApp.newTrigger("postDelayedUrlReplies").timeBased().everyMinutes(10).create();
  ScriptApp.newTrigger("dailyObservationLog").timeBased().everyDays(1).atHour(23).nearMinute(35).create();
  ScriptApp.newTrigger("syncDataToGitHub").timeBased().everyDays(1).atHour(23).nearMinute(40).create();
  ScriptApp.newTrigger("checkHealth").timeBased().everyDays(1).atHour(23).nearMinute(45).create();
  ScriptApp.newTrigger("refreshToken").timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  ScriptApp.newTrigger("pullBatchFromGitHub").timeBased().onWeekDay(ScriptApp.WeekDay.SUNDAY).atHour(21).create();
  Logger.log("triggers installed: postScheduled 08:00/12:00/16:00/19:00/22:00 daily, collectInsights 23:30 daily, detectExternalReplies every10min, syncReplyCandidatesToGitHub every10min, postDelayedUrlReplies every10min, pullGeneratedRepliesFromGitHub hourly, dailyObservationLog 23:35 daily, syncDataToGitHub 23:40 daily, checkHealth 23:45 daily, refreshToken Mon 07:00, pullBatchFromGitHub Sun 21:00");
}

// Daily (Phase2, 2026-07-26notekaigi): re-aggregates INSIGHTS_SHEET_NAME into
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
//   - no queue rows with ステータス = エラー scheduled within the last ERROR_ALERT_WINDOW_DAYS
//     （2026-09-29追加: 古いエラー行を無期限に毎日再アラートし続けないための窓。
//     2026-09-19 22:00の投稿がurlfetch日次上限超過で失敗した行が、10日以上経っても
//     直り続けアラートし続けていたのが発覚した実例あり。行自体は削除せず残す
//     ＝過去の記録として、あくまでメールを送り続けない範囲だけ絞る）
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

  const expectedTriggers = ["postScheduled", "collectInsights", "detectExternalReplies", "postDelayedUrlReplies", "dailyObservationLog", "syncDataToGitHub", "syncReplyCandidatesToGitHub", "checkHealth", "pullGeneratedRepliesFromGitHub", "refreshToken", "pullBatchFromGitHub"];
  const installed = ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); });
  expectedTriggers.forEach(function (fn) {
    if (installed.indexOf(fn) === -1) problems.push("トリガー未設定: " + fn + "（installTriggers()を再実行してください）");
  });

  if (!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OBS_SHEET_NAME)) {
    problems.push('シート "' + OBS_SHEET_NAME + '" が見つかりません（dailyObservationLog用・作成してください）');
  }
  if (!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(REPLY_QUEUE_SHEET_NAME)) {
    problems.push('シート "' + REPLY_QUEUE_SHEET_NAME + '" が見つかりません（detectExternalReplies用・作成してください）');
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    problems.push('シート "' + SHEET_NAME + '" が見つかりません');
  } else {
    const data = sheet.getDataRange().getValues();
    const now = new Date();
    const graceMs = 2 * 60 * 60 * 1000; // 2 hours
    const ERROR_ALERT_WINDOW_DAYS = 3;
    const errorWindowMs = ERROR_ALERT_WINDOW_DAYS * 24 * 60 * 60 * 1000;
    let stuck = 0;
    const recentErrors = [];
    for (let r = 1; r < data.length; r++) {
      const row = data[r];
      const scheduledAt = row[COL.DATETIME - 1];
      const status = row[COL.STATUS - 1];
      if (status === "エラー" && scheduledAt instanceof Date && (now - scheduledAt) <= errorWindowMs) {
        const when = Utilities.formatDate(scheduledAt, Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm");
        recentErrors.push(when + "：" + String(row[COL.POST_ID - 1] || "").slice(0, 150));
      }
      if (!(scheduledAt instanceof Date)) continue;
      if (status !== "投稿済み" && status !== "エラー" && (now - scheduledAt) > graceMs) stuck++;
    }
    if (stuck > 0) problems.push("投稿予定時刻を2時間以上過ぎても未処理の行が" + stuck + "件あります");
    if (recentErrors.length > 0) {
      problems.push("ステータスが「エラー」の行が直近" + ERROR_ALERT_WINDOW_DAYS + "日以内に"
        + recentErrors.length + "件あります:\n  - " + recentErrors.join("\n  - "));
    }
  }

  if (problems.length > 0) {
    const body = problems.join("\n");
    MailApp.sendEmail(Session.getEffectiveUser().getEmail(), "[MBTICODE Threads] 監視アラート", body);
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
      let replyId = "";
      const replyText = row[COL.REPLY - 1];
      if (replyText && !/https?:\/\//.test(replyText)) {
        replyId = publishText(token, userId, replyText, mainId);
      }
      // URL replies are posted later by postDelayedUrlReplies(), not here.
      sheet.getRange(r + 1, COL.STATUS).setValue("投稿済み");
      sheet.getRange(r + 1, COL.POST_ID).setValue(mainId);
      if (replyId) sheet.getRange(r + 1, COL.REPLY_POST_ID).setValue(replyId);
    } catch (e) {
      sheet.getRange(r + 1, COL.STATUS).setValue("エラー");
      sheet.getRange(r + 1, COL.POST_ID).setValue(String(e.message).slice(0, 200));
    }
  }
}

// Fires every 10 minutes (installTriggers). Posts any リプライ本文 that
// postScheduled() skipped because it contained a URL, once the main post is
// at least this old (2026-09-19 user request: URL self-replies should land
// ~2h after the main post, not seconds after it). Also handles 列J（URL自己
// リプライ本文, 2026-09-29追加）on the same delay. Actual send time is
// 2h00m-2h10m after the main post depending on where in the polling cycle it
// falls.
const URL_REPLY_DELAY_MS = 2 * 60 * 60 * 1000;

function postDelayedUrlReplies() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  const userId = props.getProperty("THREADS_USER_ID");
  if (!token || !userId) { Logger.log("postDelayedUrlReplies: setup() not run"); return; }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const now = new Date();

  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    if (row[COL.STATUS - 1] !== "投稿済み") continue;
    const replyText = row[COL.REPLY - 1];
    if (!replyText || !/https?:\/\//.test(replyText)) continue;
    if (row[COL.REPLY_POST_ID - 1]) continue; // already sent (or already flagged as errored)
    const postedAt = row[COL.DATETIME - 1];
    const mainId = row[COL.POST_ID - 1];
    if (!(postedAt instanceof Date) || !mainId) continue;
    if (now - postedAt < URL_REPLY_DELAY_MS) continue;

    try {
      const replyId = publishText(token, userId, replyText, mainId);
      sheet.getRange(r + 1, COL.REPLY_POST_ID).setValue(replyId);
      Logger.log("postDelayedUrlReplies: posted reply for " + mainId);
    } catch (e) {
      sheet.getRange(r + 1, COL.REPLY_POST_ID).setValue("エラー:" + String(e.message).slice(0, 200));
      Logger.log("postDelayedUrlReplies: failed for " + mainId + ": " + e.message);
    }
  }

  // 2本目の自己リプライ（URL誘導専用・列J/K・2026-09-29追加）。
  // 列C（1本目の自己リプライ）が続き型の本文分割などで既に使われている投稿でも、
  // 判定を待たず計画的にURL誘導を仕込めるようにする（リスト型向けの実績ベースの
  // 先回り版。反響を見てから動く旧checkEarlyPerformanceは2026-09-29に廃止済み）。
  // 1本目があればその返信（REPLY_POST_ID）に、なければ本編（mainId）にぶら下げる。
  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    if (row[COL.STATUS - 1] !== "投稿済み") continue;
    const urlReplyText = row[COL.URL_REPLY - 1];
    if (!urlReplyText) continue;
    if (row[COL.URL_REPLY_ID - 1]) continue; // already sent (or already flagged as errored)
    const postedAt = row[COL.DATETIME - 1];
    const mainId = row[COL.POST_ID - 1];
    if (!(postedAt instanceof Date) || !mainId) continue;
    if (now - postedAt < URL_REPLY_DELAY_MS) continue;

    const replyToId = row[COL.REPLY_POST_ID - 1] || mainId;
    try {
      const urlReplyId = publishText(token, userId, urlReplyText, replyToId);
      sheet.getRange(r + 1, COL.URL_REPLY_ID).setValue(urlReplyId);
      Logger.log("postDelayedUrlReplies: posted 2nd(URL) reply for " + mainId);
    } catch (e) {
      sheet.getRange(r + 1, COL.URL_REPLY_ID).setValue("エラー:" + String(e.message).slice(0, 200));
      Logger.log("postDelayedUrlReplies: 2nd(URL) reply failed for " + mainId + ": " + e.message);
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
    Logger.log("row " + (r + 1) + ": status=[" + row[COL.STATUS - 1] + "] postId=[" + row[COL.POST_ID - 1] + "]");
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
    // used to seed engagement, or a manual follow-up reply). A flat "-1"
    // undercounted these in practice, so pull the actual reply list and
    // exclude every entry Threads itself flags as our own via
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

// Every 10 minutes: scans 投稿済み posts from the last EXTERNAL_REPLY_LOOKBACK_DAYS
// days for external replies (is_reply_owned_by_me = false) not already in
// REPLY_QUEUE_SHEET_NAME, and appends one row per new reply with ステータス=未処理.
// Detection only -- no reply text is generated here (see
// syncReplyCandidatesToGitHub / sns_post_cheatsheet.md「外部リプライ自動応答」for
// where drafting happens). Polls this often so a reply is picked up quickly
// even though the drafting routine itself can only run hourly (platform cron
// minimum).
// 2026-09-21: previously scanned every 投稿済み row ever (unbounded), which hit
// the urlfetch daily quota once the queue passed ~140 posted rows (see
// EXTERNAL_REPLY_LOOKBACK_DAYS comment above). Old posts essentially never
// receive new external replies, so bounding the scan to a recent window is safe.
function detectExternalReplies() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  if (!token) { Logger.log("detectExternalReplies: setup() not run"); return; }

  const queueSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const replyQueueSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(REPLY_QUEUE_SHEET_NAME);
  if (!replyQueueSheet) { Logger.log('ERROR: sheet "' + REPLY_QUEUE_SHEET_NAME + '" not found. Create it first.'); return; }

  const existingIds = {};
  const existingData = replyQueueSheet.getDataRange().getValues();
  for (let r = 1; r < existingData.length; r++) {
    const id = existingData[r][RCOL.REPLY_ID - 1];
    if (id) existingIds[id] = true;
  }

  const windowStart = new Date(Date.now() - EXTERNAL_REPLY_LOOKBACK_DAYS * 24 * 60 * 60 * 1000);
  const queueData = queueSheet.getDataRange().getValues();
  let added = 0;
  for (let r = 1; r < queueData.length; r++) {
    const row = queueData[r];
    if (row[COL.STATUS - 1] !== "投稿済み") continue;
    const postId = row[COL.POST_ID - 1];
    if (!postId) continue;
    const postedAt = row[COL.DATETIME - 1];
    if (postedAt instanceof Date && postedAt < windowStart) continue;

    let replies;
    try {
      replies = fetchExternalReplies(postId, token);
    } catch (e) {
      Logger.log("detectExternalReplies: fetch failed for " + postId + ": " + e.message);
      continue;
    }

    replies.forEach(function (rep) {
      if (existingIds[rep.id]) return;
      const targetRow = replyQueueSheet.getLastRow() + 1;
      replyQueueSheet.getRange(targetRow, RCOL.REPLY_ID).setValue(rep.id);
      replyQueueSheet.getRange(targetRow, RCOL.POST_ID).setValue(postId);
      replyQueueSheet.getRange(targetRow, RCOL.POST_BODY).setValue(row[COL.TEXT - 1] || "");
      replyQueueSheet.getRange(targetRow, RCOL.AUTHOR).setValue(rep.username || "");
      replyQueueSheet.getRange(targetRow, RCOL.REPLY_TEXT).setValue(rep.text || "");
      replyQueueSheet.getRange(targetRow, RCOL.RECEIVED_AT).setValue(new Date());
      replyQueueSheet.getRange(targetRow, RCOL.STATUS).setValue("未処理");
      existingIds[rep.id] = true;
      added++;
    });
  }
  Logger.log("detectExternalReplies: " + added + " new external repl(y/ies) queued");
}

// Returns [{id, text, username, timestamp}] for replies NOT posted by our own
// account. Mirrors fetchExternalReplyCount but keeps the full objects instead
// of just a count.
function fetchExternalReplies(mediaId, token) {
  const uri = BASE + "/" + mediaId + "/replies?fields=id,text,username,timestamp,is_reply_owned_by_me&access_token=" + encodeURIComponent(token);
  const resp = UrlFetchApp.fetch(uri, { muteHttpExceptions: true });
  const body = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 300) {
    throw new Error("Threads API error: " + (body.error ? body.error.message : resp.getContentText()));
  }
  const list = body.data || [];
  return list.filter(function (r) { return !r.is_reply_owned_by_me; });
}

// Every 10 minutes (same cadence as detectExternalReplies): mirrors 未処理
// rows in REPLY_QUEUE_SHEET_NAME to GitHub so the scheduled reply-drafting
// cloud routine can read them without direct Sheets API access (same
// reasoning as syncDataToGitHub -- the routine's sandbox cannot reach
// script.google.com). Syncing this often keeps the file fresh for whenever
// the hourly routine happens to wake up.
function syncReplyCandidatesToGitHub() {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!token) { Logger.log("ERROR: GITHUB_TOKEN not set. Run setupGithubToken() first."); return; }
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(REPLY_QUEUE_SHEET_NAME);
  if (!sheet) { Logger.log('ERROR: sheet "' + REPLY_QUEUE_SHEET_NAME + '" not found.'); return; }

  const data = sheet.getDataRange().getValues();
  const candidates = [];
  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    if (row[RCOL.STATUS - 1] !== "未処理") continue;
    candidates.push({
      reply_id: row[RCOL.REPLY_ID - 1],
      post_id: row[RCOL.POST_ID - 1],
      post_body: row[RCOL.POST_BODY - 1],
      author: row[RCOL.AUTHOR - 1],
      reply_text: row[RCOL.REPLY_TEXT - 1],
      received_at: row[RCOL.RECEIVED_AT - 1] instanceof Date
        ? Utilities.formatDate(row[RCOL.RECEIVED_AT - 1], Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm")
        : String(row[RCOL.RECEIVED_AT - 1])
    });
  }

  try {
    githubPutFile(GITHUB_REPLY_CANDIDATES_PATH, { generated_at: new Date().toISOString(), candidates: candidates },
      "Sync reply candidates (" + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd") + ")");
    Logger.log("syncReplyCandidatesToGitHub: OK, " + candidates.length + " candidate(s)");
  } catch (e) {
    Logger.log("syncReplyCandidatesToGitHub: ERROR " + e.message);
  }
}

// Hourly: reads GITHUB_PENDING_REPLIES_PATH ({"replies":[{reply_id, reply_text}, ...]}),
// posts each drafted reply (as a reply-to-reply, keeping it in the same
// thread), updates the matching REPLY_QUEUE_SHEET_NAME row, then deletes the
// consumed file (consume-once, same as pullBatchFromGitHub).
function pullGeneratedRepliesFromGitHub() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("THREADS_ACCESS_TOKEN");
  const userId = props.getProperty("THREADS_USER_ID");
  const githubToken = props.getProperty("GITHUB_TOKEN");
  if (!token || !userId) { Logger.log("pullGeneratedRepliesFromGitHub: setup() not run"); return; }
  if (!githubToken) { Logger.log("ERROR: GITHUB_TOKEN not set."); return; }

  let file;
  try {
    file = githubGetFile(GITHUB_PENDING_REPLIES_PATH);
  } catch (e) {
    Logger.log("pullGeneratedRepliesFromGitHub: ERROR fetching file: " + e.message);
    return;
  }
  if (!file) { Logger.log("pullGeneratedRepliesFromGitHub: no pending file found, nothing to do"); return; }

  let payload;
  try {
    const jsonStr = Utilities.newBlob(Utilities.base64Decode(file.content.replace(/\n/g, ""))).getDataAsString("UTF-8");
    payload = JSON.parse(jsonStr);
  } catch (e) {
    Logger.log("pullGeneratedRepliesFromGitHub: ERROR parsing JSON: " + e.message);
    return;
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(REPLY_QUEUE_SHEET_NAME);
  if (!sheet) { Logger.log('ERROR: sheet "' + REPLY_QUEUE_SHEET_NAME + '" not found.'); return; }
  const data = sheet.getDataRange().getValues();
  const rowByReplyId = {};
  for (let r = 1; r < data.length; r++) {
    const id = data[r][RCOL.REPLY_ID - 1];
    if (id) rowByReplyId[id] = r + 1;
  }

  let posted = 0, skipped = 0;
  (payload.replies || []).forEach(function (item) {
    const rowNum = rowByReplyId[item.reply_id];
    if (!rowNum) { skipped++; return; }
    if (sheet.getRange(rowNum, RCOL.STATUS).getValue() !== "未処理") { skipped++; return; }
    try {
      const replyPostId = publishText(token, userId, item.reply_text, item.reply_id);
      sheet.getRange(rowNum, RCOL.STATUS).setValue("投稿済み");
      sheet.getRange(rowNum, RCOL.GENERATED_REPLY).setValue(item.reply_text);
      sheet.getRange(rowNum, RCOL.REPLY_POST_ID).setValue(replyPostId);
      posted++;
    } catch (e) {
      sheet.getRange(rowNum, RCOL.STATUS).setValue("エラー");
      sheet.getRange(rowNum, RCOL.GENERATED_REPLY).setValue(item.reply_text);
      sheet.getRange(rowNum, RCOL.REPLY_POST_ID).setValue(String(e.message).slice(0, 200));
      Logger.log("pullGeneratedRepliesFromGitHub: post failed for " + item.reply_id + ": " + e.message);
    }
  });

  try {
    githubDeleteFile(GITHUB_PENDING_REPLIES_PATH, file.sha,
      "Consume pending reply posts (" + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd") + ")");
  } catch (e) {
    Logger.log("pullGeneratedRepliesFromGitHub: WARNING failed to delete consumed file: " + e.message);
  }
  Logger.log("pullGeneratedRepliesFromGitHub: posted=" + posted + " skipped=" + skipped);
}

// Weekly refresh, mirrors tools/threads_connect_test.ps1 -Step refresh.
// The new token is written straight to Script Properties, never logged.
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
