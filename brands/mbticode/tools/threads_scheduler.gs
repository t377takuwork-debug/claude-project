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
//   3. installTriggers() - creates the 08:00 / 12:00 / 22:00 posting triggers,
//      the daily 23:30 insight-collection / 23:35 observation-log / 23:40
//      GitHub-sync triggers, the weekly (Mon 07:00) token refresh trigger, and
//      the weekly (Sun 21:00) GitHub batch-pull trigger.
//
// Sheet: a tab named exactly SHEET_NAME, row 1 = header, columns in this order:
//   投稿日時 | 本文 | リプライ本文 | 型 | FW | ステータス | 投稿ID | リプライ投稿ID
// 投稿日時 must be an actual Date/time cell (not plain text) so comparisons work.
// 型・FW are free-text tags (e.g. "型B", "MBTI(ESFJ)") copied from posts_threads.txt
// when the row is created; used later to correlate insights with content category.
// ステータス starts empty/"未投稿"; this script writes "投稿済み" or "エラー".
//
// Insight tab: a tab named exactly INSIGHTS_SHEET_NAME, row 1 = header:
//   投稿ID | 投稿日時 | 型 | FW | Views | Likes | Replies | Reposts | Quotes | 取得日時
// One row per post, overwritten in place each day collectInsights() runs
// (a snapshot of "latest known numbers", not a full history timeline).
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
const COL = { DATETIME: 1, TEXT: 2, REPLY: 3, TYPE: 4, FW: 5, STATUS: 6, POST_ID: 7, REPLY_POST_ID: 8 };
const ICOL = { POST_ID: 1, DATETIME: 2, TYPE: 3, FW: 4, VIEWS: 5, LIKES: 6, REPLIES: 7, REPOSTS: 8, QUOTES: 9, FETCHED_AT: 10 };
const OCOL = {
  DATE: 1, POST_COUNT: 2, VIEWS: 3, LIKES: 4, REPLIES: 5, REPOSTS: 6, QUOTES: 7,
  ENGAGEMENT_RATE: 8, REPLY_RATE: 9, LIKE_RATE: 10, REPOST_RATE: 11, RECORDED_AT: 12
};
const BASE = "https://graph.threads.net/v1.0";

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
  [8, 12, 22].forEach(function (hour) {
    ScriptApp.newTrigger("postScheduled").timeBased().everyDays(1).atHour(hour).nearMinute(0).create();
  });
  ScriptApp.newTrigger("collectInsights").timeBased().everyDays(1).atHour(23).nearMinute(30).create();
  ScriptApp.newTrigger("dailyObservationLog").timeBased().everyDays(1).atHour(23).nearMinute(35).create();
  ScriptApp.newTrigger("syncDataToGitHub").timeBased().everyDays(1).atHour(23).nearMinute(40).create();
  ScriptApp.newTrigger("checkHealth").timeBased().everyDays(1).atHour(23).nearMinute(45).create();
  ScriptApp.newTrigger("refreshToken").timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  ScriptApp.newTrigger("pullBatchFromGitHub").timeBased().onWeekDay(ScriptApp.WeekDay.SUNDAY).atHour(21).create();
  Logger.log("triggers installed: postScheduled 08:00/12:00/22:00 daily, collectInsights 23:30 daily, dailyObservationLog 23:35 daily, syncDataToGitHub 23:40 daily, checkHealth 23:45 daily, refreshToken Mon 07:00, pullBatchFromGitHub Sun 21:00");
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

  const expectedTriggers = ["postScheduled", "collectInsights", "dailyObservationLog", "syncDataToGitHub", "checkHealth", "refreshToken", "pullBatchFromGitHub"];
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
      if (replyText) {
        replyId = publishText(token, userId, replyText, mainId);
      }
      sheet.getRange(r + 1, COL.STATUS).setValue("投稿済み");
      sheet.getRange(r + 1, COL.POST_ID).setValue(mainId);
      if (replyId) sheet.getRange(r + 1, COL.REPLY_POST_ID).setValue(replyId);
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
    // including our own seeding self-reply (row[COL.REPLY_POST_ID]) —
    // subtract it so reply_rate/engagement_rate reflect real audience reactions only.
    let replies = metrics.replies || 0;
    if (row[COL.REPLY_POST_ID - 1]) replies = Math.max(0, replies - 1);

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
