 SELECT  *,
            SUM(CASE WHEN PracStaff > 0 AND NonPracStaff > 0 Then 1 ELSE 0 END) AS '#Mixed'
    FROM (
        SELECT  strftime('%m',report_views.visitdate) AS 'Month',
                SUM(CASE WHEN user_card.practicestaff = 1 THEN 1 ELSE 0 END) AS 'PracStaff',
                SUM(CASE WHEN user_card.practicestaff = 0 THEN 1 ELSE 0 END) AS 'NonPracStaff'
        FROM    report_views, org_card, user_card   
        WHERE   org_card.marketcode = "US"
            AND org_card.orgid = report_views.orgid
            AND user_card.userid = report_views.userid
            AND org_card.status ="Active"
            AND report_views.visitdate > '2020-12-31'
        GROUP BY strftime('%m',report_views.visitdate)
    ) 