"""draft_parts.py の部品が、今のdraftの中身と1文字も違わないことを確認する（部品を直したら必ず実行）

実行: python tools/test_draft_parts.py
各部品を作り直し、drafts/内の記事にそのまま含まれているかを調べる。含まれていなければ「デザインが変わった」ということなので失敗とする。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_parts import *  # noqa

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts')


def rd(n):
    return io.open(os.path.join(D, n), encoding='utf-8').read()


cdtv, venue, star = rd('draft_cdtv.txt'), rd('draft_venue101.txt'), rd('draft_star.txt')
fails = []


def chk(name, part, text):
    if part.rstrip() not in text:
        fails.append(name)


# ---- CDTV
chk('cdtv_artist_card(badgeあり)', cdtv_artist_card('EXILE', 'EXILEフェス', '全13曲を披露。「Choo Choo TRAIN」「Rising Sun」「I Wish For You」「Lovers Again」を含みます。'), cdtv)
chk('cdtv_artist_card(badgeなし)', cdtv_artist_card('TMG', '', '「SAYONARA (feat. Ado)」を披露します。Adoの出演はありません。'), cdtv)
chk('cdtv_order_row', cdtv_order_row('19:00', 'AI', '「ハピネス」（オープニングメガヒットLIVE）'), cdtv)
front = [('19:00', 'AI', '「ハピネス」（オープニングメガヒットLIVE）'),
         ('19:10', 'Snow Man', '「グッタイム」（月間ランキング26位として紹介。番組前半で最も投稿が伸びた枠）'),
         ('19:15', 'FRUITS ZIPPER', '「センセーション」（テレビ初・フルサイズ）'),
         ('19:21', '&amp;TEAM', '「Good Boy (Japanese ver.)」（フルサイズ）'),
         ('19:34', 'LDH選抜', "「It's Me」（ILLITの楽曲・踊ってみた企画）"),
         ('19:40', 'LiSA', '「ソフィリア」（テレビ初・フルサイズ）'),
         ('19:49', 'MAZZEL×STARGLOW', '「Nameless MythS」（コラボ・テレビ初・フルサイズ）')]
chk('cdtv_order_block(前半)', cdtv_order_block('19:00〜19:55（前半）', front), cdtv)
chk('cdtv_past_full_card(9/14)', cdtv_past_full_card(
    '2026年9月14日', '2026年9月14日', '前半',
    'KO1KEYZ「KO1KEYZ」（デビュー曲・テレビ初フルサイズ）/ LIL LEAGUE「僕を探してた」（テレビ初フルサイズ）/ なにわ男子「BLACK OUT MISSION」→「僕がカワイくて君がカワイくて」（2曲メドレー・テレビ初披露、早着替え演出）/ ポルノグラフィティ「はみだし御免」「アゲハ蝶」（フルサイズ2曲）/ マカロニえんぴつ「運命さがし」（フルサイズ初披露）',
    '後半', '', '9月14日放送回は、前半にKO1KEYZのデビュー曲とLIL LEAGUEがテレビ初フルサイズで続き、KO1KEYZが前半で最も投稿を集めました。なにわ男子は2曲メドレーをテレビ初披露。後半はSixTONES「Dance Forever」に投稿が集中しました。',
    back_extra_yellow='SixTONES「Dance Forever」（フルサイズ。公式単体投稿で全出演告知中最多エンゲージ、番組後半のピーク）', front_time='18:30〜'), cdtv)
chk('cdtv_past_compact(8/31)', cdtv_past_compact(
    '2026年8月31日のタイムテーブル',
    'BE:FIRST「Bye-Good-Bye」（オープニングメガヒットLIVE）/ Juice=Juice「盛れ！ミ・アモーレ」/ CANDY TUNE「総意♡So Free」（テレビ初披露）/ INI「You Know What To Do」/ 福山雅治「Squall」（2週連続出演の初週）/ 斉藤和義「黒猫のタンバリン」（新曲テレビ初披露）/ NCT WISH「BOY MEETS GIRL」（TRFのリメイク）',
    'BE:FIRST「Missing」（おかわりライブ）/ MAZZEL「So Strawberry」/ TOMORROW X TOGETHER「セツナハナビ (Setsuna Hanabi)」/ BE:FIRST「BRUCE WAYNE feat. Flo Milli, ATL Jacob」（日本のテレビ初披露）/ 斉藤和義「やさしくなりたい」（今夜の music power.）/ 最新週間ランキング TOP5（1位：TOMORROW X TOGETHER）/ Snow Man「show time...」（アルバム『AMENITY』よりテレビ初披露・白タキシード＋ハット演出、投稿が最も伸びた時間帯）', first=True), cdtv)

# ---- Venue101
chk('venue_artist_grid', venue_artist_grid([('INI', '「We Are」'), ('imase', '「風になれるはず」'), ('STU48', '「冬服に着替えたら」'), ('&amp;TEAM', '「Good Boy (Japanese ver.)」')]), venue)
chk('venue_plan_row', venue_plan_row('INI', '出演14回目で番組最多。過去13回の出演を振り返る'), venue)
chk('venue_timeline_item', venue_timeline_item('23:02頃〜 / EARLY', '≒JOY「サマーツインテール」', '1組目のライブ。ダブルセンターやツインテールの振りに触れる投稿が目立った。'), venue)
chk('venue_timeline_item(hl)', venue_timeline_item('23:26頃〜 / ★投稿急増ゾーン', 'M!LK「You!Joy!Parade!」', 'ラストのライブ。放送中の公式投稿で最も反応が大きかった（いいね約2.5万）。このあとハイタッチクイズ、≒101クイズへ。', True), venue)
chk('venue_past_row', venue_past_row('23:01頃〜', '1組目', 'Da-iCE「アンリミテッド」', '「切り込み隊長」という投稿が出て、ロングトーンと声量への称賛が続いた。'), venue)
chk('venue_past_row(hl)', venue_past_row('23:08頃〜', '2組目', 'M!LK「時空超えてユニバース」', '公式の放送中の投稿で最も反応が大きく、番組前半で最も投稿が伸びた。', True), venue)
chk('venue_past_card(9/26)', venue_past_card('2026年9月26日のタイムテーブル', 'Venue101 2026年9月26日タイムテーブル', '2026年9月26日 放送回', 'EXTRA WEEK1', [
    venue_past_row('23:00〜', 'OPENING', 'MC登場・番組スタート', '生放送スタート。'),
    venue_past_row('23:01頃〜', '1組目', 'Da-iCE「アンリミテッド」', '「切り込み隊長」という投稿が出て、ロングトーンと声量への称賛が続いた。'),
    venue_past_row('23:08頃〜', '2組目', 'M!LK「時空超えてユニバース」', '公式の放送中の投稿で最も反応が大きく、番組前半で最も投稿が伸びた。', True),
    venue_past_row('23:10頃〜', '企画', 'M!LK「時空超えてお絵かきグランプリ」', '放送中の投稿が少なく、位置は推定。終了後に絵への反応が出た。'),
    venue_past_row('23:16頃〜', '3組目', 'ONEW「エイリアンズ」', '前後に「好きすぎて滅！」のアカペラも。美声に反応が集まった。'),
    venue_past_row('23:22頃〜', '4組目', '新しい学校のリーダーズ「TTTTOKYO」', '地上波初披露との言及が多く、でんぐり返しやぱっつんに歓喜する投稿が続いた。'),
    venue_past_row('23:25頃〜', 'END', '新しい学校のリーダーズvs Da-iCE ジェスチャーゲーム対決', '放送中の投稿が少なく、位置は推定。'),
], 'M!LK「時空超えてユニバース」が最も投稿を集めた回。ONEWのアカペラと、新しい学校のリーダーズの地上波初披露にも反応が集まった。',
    '※Xのリアルタイム投稿を参考にした推定タイムラインです。お絵かきグランプリとジェスチャーゲーム対決の位置は推定を含みます。'), venue)

# ---- STAR
chk('star_timeline_item(open)', star_timeline_item('19:00頃 / OPENING', 'MC上垣皓太朗進行で2時間SPスタート', 'フジテレビに眠る名コラボ映像から始まった', 'open'), star)
chk('star_timeline_item(mid)', star_timeline_item('19:10頃', '<span style="font-weight: 800;">（VTR）宝塚歌劇団のコラボ映像</span>', '宝塚歌劇団が共演した名場面のブロックに入った'), star)
chk('star_timeline_item(last)', star_timeline_item('21:00頃 / LAST', '<span style="font-weight: 800;">エンディング</span>', '2時間SPが終了', 'last'), star)
chk('star_lineup_row', star_lineup_row('近藤真彦', '歌唱曲は後日発表', '「マッチSPメドレー」として披露される予定です'), star)
chk('star_lineup_row(tint,last)', star_lineup_row('特別企画（ドラマ名場面＆主題歌特集）', 'ドラマの名場面と主題歌をまとめて紹介', '公式の番組紹介に記載されています。詳しい内容は未発表です', True, True), star)
chk('star_schedule_block', star_schedule_block('時間帯未定', '近藤真彦（マッチSPメドレー）'), star)
lines917 = ['<strong>19:00頃 OPENING</strong>：MC上垣皓太朗進行で番組スタート、ナビゲーターに中島健人が登場',
            "<strong>19:01頃 郷ひろみ</strong>：「GOLDFINGER'99」「I'm Neo G」（メドレー。ダンサー多数を従えた振付アレンジで登場）",
            '<strong>19:05〜19:13頃 （企画）</strong>：中島健人による郷ひろみへのインタビュー（指ハートの記念撮影企画、秋の名バラード特集VTRも放送された）',
            '<strong>19:14頃 ポルノグラフィティ</strong>：「アゲハ蝶」「オー！リバル」「マスク・ド・カメロ」「THE REVO」（4曲メドレー。上垣アナが広島弁で紹介するひと幕もあった）',
            '<strong>19:31頃 加藤ミリヤ</strong>：「SAYONARAベイベー」',
            "<strong>19:35〜19:50頃 中島健人＋ジュニア・N's Performer（総勢21名）</strong>：「最初はキュン！」（『STAR』限定のスペシャルパフォーマンスで、この日いちばんの反響を集めた）",
            '<strong>19:50頃 LAST 郷ひろみ＋上垣アナ</strong>：ジャケットプレイ（フィナーレで番組を締めくくった）']
chk('star_past_card(9/17)', star_past_card('2026年9月17日', '2026.09.17', lines917,
    '💡 MC上垣皓太朗とナビゲーターの中島健人の進行で、郷ひろみのメドレーから始まった回。中島健人がジュニア21名と披露した「最初はキュン！」が最大の反響を集め、郷ひろみへのインタビューやポルノグラフィティの4曲メドレーも好評だった。※出演順は反響が集中したタイミングに基づく推定', new=True), star)

if fails:
    print('失敗（draftと一致しない部品）:', ', '.join(fails))
    sys.exit(1)
print('すべて一致（CDTV 6 / Venue101 7 / STAR 7）')
