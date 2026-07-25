// MBTICODE Threads scheduled poster + insight collector (Google Apps Script,
// bound to the queue spreadsheet)
//
// One-time setup (run these from the Apps Script editor, Run menu):
//   1. Add a tab named exactly SETUP_SHEET_NAME with:
//        A1: access_token       B1: <paste the token>
//        A2: threads_user_id    B2: <paste the numeric id>
//   2. setup() - reads B1/B2, stores them in Script Properties, then clears
//      B1/B2 so the token doesn't sit visibly in the sheet. No dialogs involved,
//      so it works regardless of which tab/window is focused when you click Run.
//   3. installTriggers() - creates the 08:00 / 12:00 / 22:00 posting triggers,
//      the daily 23:30 insight-collection trigger, and the weekly (Mon 07:00)
//      token refresh trigger.
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

const SHEET_NAME = "Threads投稿キュー";
const SETUP_SHEET_NAME = "設定";
const INSIGHTS_SHEET_NAME = "インサイト";
const COL = { DATETIME: 1, TEXT: 2, REPLY: 3, TYPE: 4, FW: 5, STATUS: 6, POST_ID: 7, REPLY_POST_ID: 8 };
const ICOL = { POST_ID: 1, DATETIME: 2, TYPE: 3, FW: 4, VIEWS: 5, LIKES: 6, REPLIES: 7, REPOSTS: 8, QUOTES: 9, FETCHED_AT: 10 };
const BASE = "https://graph.threads.net/v1.0";

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

function installTriggers() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  [8, 12, 22].forEach(function (hour) {
    ScriptApp.newTrigger("postScheduled").timeBased().everyDays(1).atHour(hour).nearMinute(0).create();
  });
  ScriptApp.newTrigger("collectInsights").timeBased().everyDays(1).atHour(23).nearMinute(30).create();
  ScriptApp.newTrigger("checkHealth").timeBased().everyDays(1).atHour(23).nearMinute(45).create();
  ScriptApp.newTrigger("refreshToken").timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  Logger.log("triggers installed: postScheduled 08:00/12:00/22:00 daily, collectInsights 23:30 daily, checkHealth 23:45 daily, refreshToken Mon 07:00");
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

  const expectedTriggers = ["postScheduled", "collectInsights", "checkHealth", "refreshToken"];
  const installed = ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); });
  expectedTriggers.forEach(function (fn) {
    if (installed.indexOf(fn) === -1) problems.push("トリガー未設定: " + fn + "（installTriggers()を再実行してください）");
  });

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

    const targetRow = existingRow[postId] || (insightSheet.getLastRow() + 1);
    insightSheet.getRange(targetRow, ICOL.POST_ID).setValue(postId);
    insightSheet.getRange(targetRow, ICOL.DATETIME).setValue(row[COL.DATETIME - 1]);
    insightSheet.getRange(targetRow, ICOL.TYPE).setValue(row[COL.TYPE - 1]);
    insightSheet.getRange(targetRow, ICOL.FW).setValue(row[COL.FW - 1]);
    insightSheet.getRange(targetRow, ICOL.VIEWS).setValue(metrics.views || 0);
    insightSheet.getRange(targetRow, ICOL.LIKES).setValue(metrics.likes || 0);
    insightSheet.getRange(targetRow, ICOL.REPLIES).setValue(metrics.replies || 0);
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
