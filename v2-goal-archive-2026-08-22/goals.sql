PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE goals (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    lifecycle     TEXT NOT NULL CHECK (lifecycle IN ('finite','continuous')),
    status        TEXT NOT NULL CHECK (status IN ('active','paused','completed','failed')),
    priority      INTEGER NOT NULL DEFAULT 0,
    metric        TEXT,
    operator      TEXT CHECK (operator IN ('>','>=','<','<=','==','!=')),
    target        REAL,
    current_value REAL NOT NULL DEFAULT 0,
    notes         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
  );
INSERT INTO goals VALUES('global-symlink-spielos-site-shayanspiel-github-io-vws28f','Global symlink ~/spielos-site → ShayanSpiel.Github.io','finite','active',0,'symlink_resolves','==',1.0,0.0,NULL,'2026-08-21T00:26:33.173Z','2026-08-21T00:26:33.173Z');
INSERT INTO goals VALUES('migrate-v1-spielos-knowledge-strategy-skills-assets-into-spielos-n7tma3','Migrate v1 SpielOS knowledge (strategy, skills, assets) into SpielOS2 Company','finite','active',0,'migration_candidates_approved','>=',1.0,0.0,NULL,'2026-08-21T00:29:15.489Z','2026-08-21T03:04:23.320Z');
INSERT INTO goals VALUES('diagnose-and-fix-opencode-host-failures-blocking-strategist-enri-ej5ynv','Diagnose and fix OpenCode host failures blocking Strategist enrichment','finite','active',1,'opencode_diagnostic_complete','>=',1.0,0.0,NULL,'2026-08-21T12:44:16.867Z','2026-08-21T20:45:33.953Z');
INSERT INTO goals VALUES('diagnose-and-fix-opencode-host-failures-blocking-strategist-enri-gy7ksz','Diagnose and fix OpenCode host failures blocking Strategist enrichment','finite','active',0,'opencode_diagnostic_complete','>=',1.0,0.0,NULL,'2026-08-21T20:36:07.557Z','2026-08-21T20:36:07.557Z');
INSERT INTO goals VALUES('system-engineer-diagnose-opencode2-uls89h','System Engineer diagnose opencode2','finite','active',0,'issues_found','>=',1.0,0.0,NULL,'2026-08-21T20:40:06.355Z','2026-08-21T20:40:06.355Z');
INSERT INTO goals VALUES('commercial-funnel-update-deslopping-ai-workers-offer-apply-first-5suv72','Commercial funnel update: DeSlopping + AI Workers offer, Apply-first conversion, /pricing/ and /apply/ pages','finite','active',10,NULL,NULL,NULL,0.0,NULL,'2026-08-21T20:48:36.891Z','2026-08-21T20:48:36.891Z');
COMMIT;
