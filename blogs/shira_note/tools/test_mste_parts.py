"""mste_parts.py の部品が、公開済みのMステ記事と1文字も違わないことを確認する（部品を直したら必ず実行）

実行: python tools/test_mste_parts.py
照合先は、gitに残っている公開済みの2版（固定のコミット）:
  10/16回（通常回・1時間枠）= 263e7ab6 ／ 10/23回（40周年SP・2時間枠・時間帯H3）= b2e92cc3
draftは毎週変わるので、現在のdraftではなくコミットと照合する。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mste_parts import *  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def show(rev):
    r = subprocess.run(['git', 'show', rev + ':blogs/shira_note/drafts/draft_mste.txt'], cwd=REPO, capture_output=True)
    assert r.returncode == 0, ('git show に失敗', rev, r.stderr[:200])
    return r.stdout.decode('utf-8').replace('\r\n', '\n')


A, B = show('263e7ab6'), show('b2e92cc3')
fails = []


def chk(name, part, text):
    if part.rstrip() not in text:
        fails.append(name)


def nok(s):
    """10/16版は行のコメントに「頃」が無い（見えないコメントだけの違い）。そろえて比べる"""
    return re.sub(r'<!-- (\d\d:\d\d)頃 ', r'<!-- \1 ', s)


# ================= 10/16版（通常回） =================
rows16 = [mste_tt_opening('21:00'),
          mste_tt_row('21:05頃', 'AI', ['まだ旅の途中']),
          mste_tt_row('21:12頃', 'EBiDAN', ['Yes! 東京'], badge='番組初出演'),
          mste_tt_row('21:20頃', 'sumika', ['エンバートーチ']),
          mste_tt_row('21:27頃', 'RADWIMPS', ['夕星-ゆうづつ-'], badge='テレビ初披露'),
          mste_tt_row('21:34頃', 'あいみょん', ['さながらロンリー']),
          mste_tt_row('21:41頃', '櫻坂46', ['愛MUST BE']),
          mste_tt_row('21:47頃', 'なにわ男子', ['Moonlit'], last=True)]
chk('tt_card(通常回・header+footer)', nok(mste_tt_card('Mステ タイムテーブル（2026年10月16日）', rows16, mste_tt_header('2026.10.16'), mste_tt_footer())), A)

chk('lineup(plain)', mste_lineup_card('AI', '「まだ旅の途中」を披露。'), A)
chk('lineup(badge)', mste_lineup_card('EBiDAN', "「Yes! 東京」を披露。15周年記念シングルで、超特急・SUPER★DRAGON・ONE N' ONLY・原因は自分にある。・BUDDiiS・ICEx・Lienelの選抜メンバーが出演。", '番組初出演'), A)
chk('lineup(badge2)', mste_lineup_card('RADWIMPS', '「夕星-ゆうづつ-」を披露。映画『汝、星のごとく』の主題歌で、テレビ初披露。', 'テレビ初披露'), A)

chk('guide', mste_guide_block('10/16', [
    ('21:00〜', 'オープニング・序盤枠', '過去5回のうち3回は、渡辺美里・福山雅治・T.M.Revolutionのようなキャリアの長い歌い手が序盤に登場しています。今回はAIが21:05頃、番組初出演のEBiDANが21:12頃に続く、というのが筆者の読みです。'),
    ('21:20頃〜', '中盤枠', 'sumika・RADWIMPS・あいみょんが続く時間帯になりそうです。RADWIMPSの「夕星-ゆうづつ-」はテレビ初披露で、映画『汝、星のごとく』の公開直後に披露されます。'),
    ('21:40頃〜', '終盤・大トリ枠', '過去5回のトリは、乃木坂46・ATEEZ・TOMORROW X TOGETHERといったグループが3回でした。残りの2回はあいみょんと、福山雅治×ポルノグラフィティです。今回は櫻坂46となにわ男子が終盤に並ぶかもしれません。')],
    '※過去5回の放送をもとにした筆者の目安です。'), A)

chk('tendency', mste_tendency_cards('Mステ 通常回のタイムテーブルの傾向と注目点', [
    ('🕒 通常放送の構成', '10月16日は21:00〜21:54の通常放送で、谷胡桃アナがサブMCとして初登場します。'),
    ('🌟 トリの予測', '過去5回のトリはグループが3回でした。今回は櫻坂46かなにわ男子が最後に来るかもしれません。'),
    ('🔍 企画コーナーのタイミング', '過去にはVTR企画が21:28頃に入った回がありました。今回のVTR企画は、まだ発表されていません。'),
    ('📱 公式SNSの連動', '公式X（旧Twitter）では放送直前や生放送中に「次は〇〇が登場！」といったリアルタイム告知が行われます。この記事でもその情報を反映します。')],
    '10月16日 21:00〜 随時更新予定'), A)

chk('faq', mste_faq_cards([
    ('10月16日の詳細なタイムテーブルは事前にわかりますか？', '公式の分刻みタイムテーブルはまだ出ていません。全7組の出演順と登場時間の目安は、21:00〜21:54の放送に合わせてこの記事でリアルタイムに更新します。'),
    ('EBiDANの出番は何時頃ですか？', '21:12頃の序盤〜中盤を予想します。過去の初出演は序盤の回も終盤の回もあり、あくまで筆者の読みです。実際の出演順は放送開始後にこの記事で更新します。'),
    ('なにわ男子の出番は何時頃ですか？', '21:47頃の大トリを予想します。過去5回のトリはグループが3回だった、というのが根拠で、あくまで筆者の読みです。実際の出演順は放送開始後にこの記事で更新します。'),
    ('録画を忘れました。見逃し配信はありますか？', 'Mステは音楽権利の都合上、TVerやABEMAなどの見逃し配信が一切ありません。放送内容は本ページの出演順・歌唱曲まとめで確認できます。'),
    ('Mステとは何の略ですか？', 'Mステは『ミュージックステーション』の略称です。テレビ朝日系列で毎週金曜よる8時から生放送されている音楽番組で、1986年の放送開始から続く長寿番組として知られています。')]), A)

chk('archive(open)', mste_archive_entry('21:00頃 / OPENING', '渡辺美里「My Revolution」', '約28年ぶりのMステ出演。番組冒頭で代表曲を披露した。', 'open'), A)
chk('archive(peak)', mste_archive_entry('21:09頃 / ★投稿のピーク', 'M!LK「時空超えてユニバース」', 'テレビ初披露。走るパートのある振りが話題になった。', 'peak'), A)
chk('archive(normal)', mste_archive_entry('21:20頃 / TALK', 'ひな壇トーク', 'M!LKのメンバーと上白石萌音の掛け合いに反応が集まった。'), A)
chk('archive(last)', mste_archive_entry('21:54頃 / ENDING', '鈴木新彩アナがサブMCを卒業', '約4年間への感謝を伝える投稿が、番組中から放送後まで続いた。', 'n', True), A)

chk('past_card(9/4)', mste_past_card(
    '2026年9月4日のタイムテーブル', '2026年9月4日 放送回（MC: タモリ / 鈴木新彩）',
    '21:05頃〜<br>\n福山雅治「虹」（約6年ぶり披露）／21:12頃〜 新しい学校のリーダーズ feat.アイナ・ジ・エンド「Sweet Memories」（TV初披露）<br><br>\n'
    '21:20頃〜<br>\nポルノグラフィティ「はみだし御免」（4年ぶり出演・TV初披露）<br><br>\n'
    '21:28頃〜<br>\nゲスト各組のMステ初出演回を振り返るVTR企画（鈴木新彩アナのサブMC卒業も生報告）<br><br>\n'
    '21:35頃〜<br>\n平井大「名残花」／絢香「みんな空の下」→「WELL-come」（6年ぶり出演）<br><br>\n'
    '21:45頃〜終盤<br>\n福山雅治「邂逅」→ポルノグラフィティ「サウダージ」★番組最大ピーク',
    '💡 各組のMステ初出演回を振り返るVTR企画に反応が集中した回。終盤の福山雅治「邂逅」からポルノグラフィティ「サウダージ」への流れと、2組の先輩後輩トークも反響の核になった。'), A)

# ================= 10/23版（2時間枠・時間帯H3） =================
pred = [('20:05頃', '郷ひろみ', ['2億4千万の瞳 -エキゾチック・ジャパン-']), ('20:14頃', 'adieu', ['ささくれ']), ('20:22頃', 'スガシカオ', ['Progress']),
        ('20:31頃', '生田斗真', ['花であることを忘れたか']), ('20:40頃', 'INI', ['You Know What To Do']), ('20:50頃', 'aiko', ['あなたの花の色']),
        ('21:00頃', 'KEY TO LIT', ['KEY TERUYA2 ～キテルヤツ～']), ('21:09頃', '湘南乃風', ['サラバ']), ('21:18頃', 'Aぇ! group', ['Emotion']),
        ('21:28頃', 'Travis Japan', ['EGO']), ('21:38頃', 'GLAY', ['誘惑', '汚れた英雄'])]
ra = [mste_tt_opening('20:00')] + [mste_tt_row(t, n, s, border=(n != 'aiko')) for t, n, s in pred[:6]]
rb = [mste_tt_row(t, n, s, last=(n == 'GLAY')) for t, n, s in pred[6:]]
chk('tt_card(20時台・headerのみ)', mste_tt_card('Mステ タイムテーブル（2026年10月23日）', ra, header=mste_tt_header('2026.10.23')), B)
chk('tt_card(21時台・footerのみ)', mste_tt_card('Mステ タイムテーブル（2026年10月23日 21時台）', rb, footer=mste_tt_footer()), B)
chk('h3', mste_h3('20時台のタイムテーブル（予想）'), B)
chk('lineup(GLAY)', mste_lineup_card('GLAY', '「誘惑」「汚れた英雄」の2曲を披露。「誘惑」は代表曲で、「汚れた英雄」は最新シングル。'), B)

ents = [mste_archive_entry('21:00頃 / OPENING ★投稿のピーク', 'EBiDAN「Yes! 東京」', '番組初出演。階段降りの演出と各グループの紹介で15周年を祝い、超特急・ユーキの言葉に感動の投稿が集まった。Lienelの芳賀柊斗は体調不良で欠席し、近藤駿太が代打で出演した。', 'peak'),
        mste_archive_entry('21:08頃 / LIVE', 'あいみょん「さながらロンリー」', 'フード付きの衣装に好意的な声が集まった。'),
        mste_archive_entry('21:44頃 / ★投稿のピーク', '櫻坂46「愛MUST BE」', '谷口愛季がセンター。ドレス衣装とバレエ調のダンス、長机を囲む特別セットでMVの世界観を再現した。', 'peak'),
        mste_archive_entry('21:54頃 / ENDING', '谷胡桃アナがサブMCとして初登場', '緊張気味の進行に「頑張って」と励ます投稿が続いた。', 'n', True)]
for i, e in enumerate(ents):
    chk('archive(10/23版 ' + str(i) + ')', e, B)

chk('past_card(9/18)', mste_past_card(
    '2026年9月18日のタイムテーブル', '2026年9月18日 放送回（MC: タモリ / 鈴木新彩）',
    '21:00頃〜<br>\n渡辺美里「My Revolution」（約28年ぶり出演・オープニング）<br><br>\n'
    '21:09頃〜<br>\nM!LK「時空超えてユニバース」（TV初披露）★投稿のピーク／21:27頃〜 上白石萌音「Trophy」<br><br>\n'
    '21:35頃〜<br>\n中島健人「鬼事」★投稿のピーク<br><br>\n'
    '21:45頃〜終盤<br>\nTHE SPELLBOUND×BOOM BOOM SATELLITES「KICK IT OUT」（初出演）／21:50頃〜 あいみょん「マリーゴールド」→「今日は晴れ、肌寒い。私は家、ギターを弾く。」',
    '💡 M!LKのTV初披露と中島健人「鬼事」の赤鬼パフォーマンスに反応が集中した回。THE SPELLBOUND×BOOM BOOM SATELLITESの完全生演奏や、鈴木新彩アナのサブMC卒業にも声が続いた。'), B)

if fails:
    print('NG（公開済みの記事と一致しない部品）:')
    for f in fails:
        print('  - ' + f)
    sys.exit(1)
print('OK: 全部品が公開済みの記事（10/16版・10/23版）と一致')
