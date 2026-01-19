-- ============================================================
-- データベースインデックス設定ファイル
-- ============================================================
-- このファイルには、パフォーマンス向上のための適切なインデックスが定義されています。
-- 実行前に、既存のインデックスを確認し、重複を避けてください。
-- 
-- 実行方法:
--   psql -U toudai -d spotlight -f database_indexes.sql
-- ============================================================

-- ============================================================
-- 1. userテーブル
-- ============================================================

-- usernameでの検索（ユーザープロフィール取得など）
-- 使用クエリ例: SELECT * FROM "user" WHERE username = %s
CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);

-- adminフラグでの検索（管理者認証など）
-- 使用クエリ例: SELECT admin FROM "user" WHERE userID = %s
-- 注: userIDはPRIMARY KEYのため、既にインデックスが存在

-- idカラムでのソート（管理者画面でのユーザー一覧取得）
-- 使用クエリ例: SELECT * FROM "user" ORDER BY id ASC LIMIT 300 OFFSET %s
CREATE INDEX IF NOT EXISTS idx_user_id ON "user"(id);


-- ============================================================
-- 2. contentテーブル
-- ============================================================

-- userIDでの検索（ユーザーが投稿したコンテンツ一覧取得）
-- 使用クエリ例: SELECT * FROM content WHERE userID = %s ORDER BY posttimestamp DESC
CREATE INDEX IF NOT EXISTS idx_content_userid ON content(userID);
CREATE INDEX IF NOT EXISTS idx_content_userid_timestamp ON content(userID, posttimestamp DESC);

-- posttimestampでのソート（新着順取得など）
-- 使用クエリ例: SELECT * FROM content ORDER BY posttimestamp DESC
CREATE INDEX IF NOT EXISTS idx_content_posttimestamp ON content(posttimestamp DESC);

-- textflagでのフィルタリング（ランダム取得でテキスト投稿を除外）
-- 使用クエリ例: SELECT * FROM content WHERE textflag = FALSE OR textflag IS NULL
CREATE INDEX IF NOT EXISTS idx_content_textflag ON content(textflag) WHERE textflag = FALSE OR textflag IS NULL;

-- contentpathでのLIKE検索（ファイル名からコンテンツ検索）
-- 使用クエリ例: SELECT * FROM content WHERE contentpath LIKE %s
-- 注: LIKE検索はインデックスの効果が限定的ですが、部分一致検索のパフォーマンス向上に寄与
CREATE INDEX IF NOT EXISTS idx_content_contentpath ON content(contentpath);

-- tagでの検索（検索機能）
-- 使用クエリ例: SELECT * FROM content WHERE tag ILIKE %s
-- 注: ILIKE検索はインデックスの効果が限定的ですが、検索パフォーマンス向上に寄与
CREATE INDEX IF NOT EXISTS idx_content_tag ON content(tag) WHERE tag IS NOT NULL;

-- titleでの検索（検索機能）
-- 使用クエリ例: SELECT * FROM content WHERE title ILIKE %s
CREATE INDEX IF NOT EXISTS idx_content_title ON content(title);

-- spotlightnumでのソート（人気順取得など）
-- 使用クエリ例: SELECT * FROM content ORDER BY spotlightnum DESC
CREATE INDEX IF NOT EXISTS idx_content_spotlightnum ON content(spotlightnum DESC);

-- playnumでのソート（再生回数順取得など）
-- 使用クエリ例: SELECT * FROM content ORDER BY playnum DESC
CREATE INDEX IF NOT EXISTS idx_content_playnum ON content(playnum DESC);

-- contentIDでの範囲検索（ループ判定など）
-- 使用クエリ例: SELECT MIN(contentID), MAX(contentID) FROM content WHERE ...
-- 注: contentIDはPRIMARY KEYのため、既にインデックスが存在


-- ============================================================
-- 3. commentテーブル
-- ============================================================

-- contentIDでの検索（コンテンツのコメント一覧取得）
-- 使用クエリ例: SELECT * FROM comment WHERE contentID = %s ORDER BY commenttimestamp ASC
CREATE INDEX IF NOT EXISTS idx_comment_contentid ON comment(contentID);
CREATE INDEX IF NOT EXISTS idx_comment_contentid_timestamp ON comment(contentID, commenttimestamp ASC);

-- userIDでの検索（ユーザーが投稿したコメント一覧取得）
-- 使用クエリ例: SELECT * FROM comment WHERE userID = %s
CREATE INDEX IF NOT EXISTS idx_comment_userid ON comment(userID);

-- commenttimestampでのソート
-- 使用クエリ例: SELECT * FROM comment ORDER BY commenttimestamp ASC
CREATE INDEX IF NOT EXISTS idx_comment_timestamp ON comment(commenttimestamp ASC);

-- parentcommentIDでの検索（返信コメントの取得）
-- 使用クエリ例: SELECT * FROM comment WHERE parentcommentID = %s
CREATE INDEX IF NOT EXISTS idx_comment_parentid ON comment(parentcommentID) WHERE parentcommentID IS NOT NULL;

-- contentIDでのカウント（コメント数取得）
-- 使用クエリ例: SELECT COUNT(*) FROM comment WHERE contentID = %s
-- 注: idx_comment_contentidが使用される


-- ============================================================
-- 4. contentuserテーブル
-- ============================================================

-- (contentID, userID)での検索（スポットライトフラグ取得など）
-- 使用クエリ例: SELECT spotlightflag FROM contentuser WHERE contentID = %s AND userID = %s
-- 注: (contentID, userID)はPRIMARY KEYのため、既にインデックスが存在

-- userIDとspotlightflagでの検索（スポットライト済みコンテンツ一覧取得）
-- 使用クエリ例: SELECT * FROM contentuser WHERE userID = %s AND spotlightflag = TRUE
CREATE INDEX IF NOT EXISTS idx_contentuser_userid_spotlight ON contentuser(userID, spotlightflag) WHERE spotlightflag = TRUE;

-- contentIDとuserIDでの更新（スポットライトON/OFF）
-- 使用クエリ例: UPDATE contentuser SET spotlightflag = TRUE WHERE contentID = %s AND userID = %s
-- 注: PRIMARY KEYのインデックスが使用される

-- notifiedフラグでの検索（通知送信済みチェック）
-- 使用クエリ例: SELECT notified FROM contentuser WHERE contentID = %s AND userID = %s
-- 注: PRIMARY KEYのインデックスが使用される


-- ============================================================
-- 5. playlistテーブル
-- ============================================================

-- userIDでの検索（ユーザーのプレイリスト一覧取得）
-- 使用クエリ例: SELECT * FROM playlist WHERE userID = %s ORDER BY playlistID
-- 注: (userID, playlistID)はPRIMARY KEYのため、既にインデックスが存在


-- ============================================================
-- 6. playlistdetailテーブル
-- ============================================================

-- (userID, playlistID)での検索（プレイリスト内のコンテンツ一覧取得）
-- 使用クエリ例: SELECT * FROM playlistdetail WHERE userID = %s AND playlistID = %s
-- 注: (userID, playlistID, contentID)はPRIMARY KEYのため、既にインデックスが存在

-- contentIDでの検索（コンテンツが含まれるプレイリスト検索など）
-- 使用クエリ例: SELECT * FROM playlistdetail WHERE contentID = %s
CREATE INDEX IF NOT EXISTS idx_playlistdetail_contentid ON playlistdetail(contentID);


-- ============================================================
-- 7. serchhistoryテーブル
-- ============================================================

-- userIDでの検索（検索履歴一覧取得）
-- 使用クエリ例: SELECT DISTINCT ON (serchword) serchword FROM serchhistory WHERE userID = %s ORDER BY serchword, serchID DESC
CREATE INDEX IF NOT EXISTS idx_serchhistory_userid ON serchhistory(userID);
CREATE INDEX IF NOT EXISTS idx_serchhistory_userid_word ON serchhistory(userID, serchword, serchID DESC);

-- (userID, serchword)でのユニーク制約チェック
-- 使用クエリ例: INSERT INTO serchhistory (userID, serchword) VALUES (%s, %s)
-- 注: UNIQUE制約が存在するため、既にインデックスが存在


-- ============================================================
-- 8. playhistoryテーブル
-- ============================================================

-- userIDでの検索（再生履歴一覧取得）
-- 使用クエリ例: SELECT * FROM playhistory WHERE userID = %s ORDER BY playID DESC LIMIT 50
CREATE INDEX IF NOT EXISTS idx_playhistory_userid ON playhistory(userID);
CREATE INDEX IF NOT EXISTS idx_playhistory_userid_playid ON playhistory(userID, playID DESC);

-- contentIDでの検索（コンテンツの再生履歴検索など）
-- 使用クエリ例: SELECT * FROM playhistory WHERE contentID = %s
CREATE INDEX IF NOT EXISTS idx_playhistory_contentid ON playhistory(contentID);

-- userIDでのカウント（再生履歴件数チェック）
-- 使用クエリ例: SELECT COUNT(*) FROM playhistory WHERE userID = %s
-- 注: idx_playhistory_useridが使用される

-- userIDでの古い順削除（再生履歴の自動削除）
-- 使用クエリ例: DELETE FROM playhistory WHERE userID = %s AND playID IN (SELECT playID FROM playhistory WHERE userID = %s ORDER BY playID ASC LIMIT 200)
-- 注: idx_playhistory_userid_playidが使用される


-- ============================================================
-- 9. notificationテーブル
-- ============================================================

-- userIDでの検索（通知一覧取得）
-- 使用クエリ例: SELECT * FROM notification WHERE userID = %s ORDER BY notificationtimestamp DESC
CREATE INDEX IF NOT EXISTS idx_notification_userid ON notification(userID);
CREATE INDEX IF NOT EXISTS idx_notification_userid_timestamp ON notification(userID, notificationtimestamp DESC);

-- isreadフラグでの検索（未読通知数取得）
-- 使用クエリ例: SELECT COUNT(*) FROM notification WHERE userID = %s AND isread = FALSE
CREATE INDEX IF NOT EXISTS idx_notification_userid_isread ON notification(userID, isread) WHERE isread = FALSE;

-- notificationtimestampでのソート
-- 使用クエリ例: SELECT * FROM notification ORDER BY notificationtimestamp DESC
CREATE INDEX IF NOT EXISTS idx_notification_timestamp ON notification(notificationtimestamp DESC);

-- (contentuserCID, contentuserUID)での外部キー検索
-- 使用クエリ例: SELECT * FROM notification WHERE contentuserCID = %s AND contentuserUID = %s
CREATE INDEX IF NOT EXISTS idx_notification_contentuser ON notification(contentuserCID, contentuserUID) WHERE contentuserCID IS NOT NULL;

-- (comCTID, comCMID)での外部キー検索
-- 使用クエリ例: SELECT * FROM notification WHERE comCTID = %s AND comCMID = %s
CREATE INDEX IF NOT EXISTS idx_notification_comment ON notification(comCTID, comCMID) WHERE comCTID IS NOT NULL;


-- ============================================================
-- 10. reportsテーブル
-- ============================================================

-- reporttimestampでのソート（通報一覧取得）
-- 使用クエリ例: SELECT * FROM reports ORDER BY reporttimestamp ASC LIMIT 300 OFFSET %s
CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(reporttimestamp ASC);

-- processflagでの検索（未処理通報の検索）
-- 使用クエリ例: SELECT * FROM reports WHERE processflag = FALSE
CREATE INDEX IF NOT EXISTS idx_reports_processflag ON reports(processflag) WHERE processflag = FALSE;

-- reportuidIDでの検索（ユーザーが送信した通報一覧）
-- 使用クエリ例: SELECT COUNT(*) FROM reports WHERE reportuidID = %s
CREATE INDEX IF NOT EXISTS idx_reports_reportuid ON reports(reportuidID);

-- targetuidIDでの検索（ユーザーが受けた通報一覧）
-- 使用クエリ例: SELECT COUNT(*) FROM reports WHERE targetuidID = %s
CREATE INDEX IF NOT EXISTS idx_reports_targetuid ON reports(targetuidID);

-- contentIDでの検索（コンテンツへの通報一覧）
-- 使用クエリ例: SELECT COUNT(*) FROM reports WHERE contentID = %s
CREATE INDEX IF NOT EXISTS idx_reports_contentid ON reports(contentID) WHERE contentID IS NOT NULL;

-- (comCTID, comCMID)での検索（コメントへの通報一覧）
-- 使用クエリ例: SELECT * FROM reports WHERE comCTID = %s AND comCMID = %s
CREATE INDEX IF NOT EXISTS idx_reports_comment ON reports(comCTID, comCMID) WHERE comCTID IS NOT NULL;

-- reporttypeでの検索（通報タイプ別検索）
-- 使用クエリ例: SELECT * FROM reports WHERE reporttype = %s
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(reporttype);


-- ============================================================
-- 11. blocklistテーブル
-- ============================================================

-- userIDでの検索（ブロックしたユーザー一覧取得）
-- 使用クエリ例: SELECT * FROM blocklist WHERE userID = %s ORDER BY blocktimestamp DESC
CREATE INDEX IF NOT EXISTS idx_blocklist_userid ON blocklist(userID);
CREATE INDEX IF NOT EXISTS idx_blocklist_userid_timestamp ON blocklist(userID, blocktimestamp DESC);

-- blockedUserIDでの検索（自分をブロックしたユーザー検索）
-- 使用クエリ例: SELECT * FROM blocklist WHERE blockedUserID = %s
CREATE INDEX IF NOT EXISTS idx_blocklist_blockeduserid ON blocklist(blockedUserID);

-- (userID, blockedUserID)でのユニーク制約チェック
-- 使用クエリ例: INSERT INTO blocklist (userID, blockedUserID) VALUES (%s, %s) ON CONFLICT DO NOTHING
-- 注: UNIQUE制約が存在するため、既にインデックスが存在

-- 両方向ブロック検索の最適化（CTEで使用される）
-- 使用クエリ例: 
--   SELECT blockedUserID AS userID FROM blocklist WHERE userID = %s
--   UNION
--   SELECT userID FROM blocklist WHERE blockedUserID = %s
-- 注: idx_blocklist_useridとidx_blocklist_blockeduseridが使用される


-- ============================================================
-- 12. 複合インデックス（複数の条件を組み合わせるクエリ用）
-- ============================================================

-- contentテーブル: userID + textflag + posttimestamp（ユーザーの投稿一覧でテキスト投稿を除外）
-- 使用クエリ例: SELECT * FROM content WHERE userID = %s AND (textflag = FALSE OR textflag IS NULL) ORDER BY posttimestamp DESC
CREATE INDEX IF NOT EXISTS idx_content_userid_textflag_timestamp ON content(userID, textflag, posttimestamp DESC) WHERE textflag = FALSE OR textflag IS NULL;

-- contentテーブル: textflag + userID（ランダム取得でテキスト投稿を除外しつつブロックユーザーを除外）
-- 使用クエリ例: SELECT * FROM content WHERE (textflag = FALSE OR textflag IS NULL) AND userID NOT IN (...)
CREATE INDEX IF NOT EXISTS idx_content_textflag_userid ON content(textflag, userID) WHERE textflag = FALSE OR textflag IS NULL;


-- ============================================================
-- 13. 統計情報の更新
-- ============================================================
-- インデックス作成後、PostgreSQLのクエリプランナーが最適なインデックスを選択できるよう、
-- 統計情報を更新することを推奨します。

-- ANALYZE;

-- ============================================================
-- インデックス確認クエリ
-- ============================================================
-- 以下のクエリで、作成されたインデックスを確認できます。
-- 
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;
-- ============================================================

