-- 016 · study_snapshot_mirror_bi 分域: 研究 manifest / 源级快照(外审第三轮窄补 #3-b 配套,2026-07-13)
-- 缘由: taosha 014 引入源级快照(content 仅 qbase 半,合法再种链第一环),发布=同一镜像+
--       attestation 机制;qbase 014 镜像触发器硬编码"须含两半"→ 源级快照发布被拒
--       (E2E Stage2b 实测: taosha snapshot_id=38 已落、镜像 INSERT 拒)。本迁移与 taosha 014
--       study_snapshot_biu 同款分域,属 #3-b 题中之义(发布机制配套面),非新增制度。
-- 分域口径(与 taosha 侧逐字对齐):
--   · content 含 taosha 键 = 研究 manifest → 两半均须在(原检查语义保留);
--   · content 仅 qbase 半 = 源级快照 → qbase 半须为非空对象即可(REQUIRED 六键完备性由
--     taosha 侧 study_snapshot_biu 已焊,镜像=逐字节副本,不重复实现,防两处口径漂移)。
-- 正向控制不弱化: 引擎不得写镜像(保留);digest 库算(保留);append-only/no-truncate 触发器
--   不动;attestation 流程不动;源级快照仍不可被引擎当研究 manifest 消费(ViewReader fail-closed)。
-- 回滚边界: study_snapshot_mirror_bi() 重放 014 定义。
-- 幂等: CREATE OR REPLACE。apply 身份 = postgres(承 014;镜像表/触发器防拆链属主,
--   qbase_app 实测非属主被拒 must be owner——防拆对施工者同样生效,照 014 先例走属主)。

CREATE OR REPLACE FUNCTION public.study_snapshot_mirror_bi() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.content->'qbase' IS NULL OR jsonb_typeof(NEW.content->'qbase') <> 'object'
     OR NEW.content->'qbase' = '{}'::jsonb THEN
    RAISE EXCEPTION '修法#2: 镜像 content 须含非空 qbase 批次向量';
  END IF;
  -- 016 分域(窄补三 #3-b): 含 taosha 键=研究 manifest(两半均须在);仅 qbase 半=源级快照
  IF NEW.content ? 'taosha' AND NEW.content->'taosha' IS NULL THEN
    RAISE EXCEPTION '修法#2: 研究 manifest 镜像 content 的 taosha 半非法';
  END IF;
  IF current_user = 'taosha_engine' THEN
    RAISE EXCEPTION '修法#2: 引擎不得写镜像(受权角色专责)';
  END IF;
  NEW.digest := encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex');
  RETURN NEW;
END $$;
COMMENT ON FUNCTION public.study_snapshot_mirror_bi() IS
  '镜像 BEFORE INSERT(修法#2 + 016 窄补三分域): 非空 qbase 半必须;含 taosha 键=研究 '
  'manifest;仅 qbase 半=源级快照(#3-b 再种链)。引擎禁写;digest 库算。';
