(function () {
  const COOKIE_NAME = "ui_locale";
  const PARAM_NAME = "ui_locale";
  const CLIENT_DICT = {
    zh: {
      scn_apollo_avatar_title: "ApolloAvatar",
      scn_apollo_avatar_desc: "数字人跟随生成",
      apollo_avatar_duration: "时长档位",
      apollo_avatar_15s: "15秒",
      apollo_avatar_30s: "30秒",
      apollo_avatar_live_toggle: "Live（计费）",
      apollo_avatar_live_hint: "开启 Live 会调用外部视频模型并产生费用；默认仅展示 demo，不计费。",
      apollo_avatar_char_image: "角色图",
      apollo_avatar_prompt: "提示词",
      apollo_avatar_ref_video: "参考视频",
      apollo_avatar_create_task: "创建任务",
      apollo_avatar_generate_demo: "生成（Demo）",
      apollo_avatar_generate_live: "生成（Live）",
      apollo_avatar_live_disabled_hint: "当前环境未开启 Live gate。",
      tab_digital_human: "数字人",
      tab_hot_follow: "热点跟随",
      hot_follow_title: "热点跟随",
      coming_soon: "敬请期待。",
      seed: "Seed（可选）",
      new_digital_human: "新建数字人",
      "tasks.wizard.title": "选择任务场景",
      "tasks.wizard.subtitle": "请选择您要创建的任务类型，每种类型都有专门优化的工作流程",
      "tasks.wizard.start": "开始创建",
      "tasks.scene.avatar.title": "数字人 IP",
      "tasks.scene.avatar.desc": "复刻真人形象，跟随视频。支持唇形同步。",
      "tasks.scene.hot.title": "热点跟拍",
      "tasks.scene.hot.desc": "拆解对标视频，像素级复刻。自动提取脚本与分镜。",
      "tasks.scene.baseline.title": "基础剪辑",
      "tasks.scene.baseline.desc": "通用剪辑流水线。去重、混剪、基础配音。",
      "tasks.wizard.hint_title": "选择提示",
      "tasks.wizard.hint_avatar": "适合需要真人出镜、品牌代言的视频内容",
      "tasks.wizard.hint_hot": "适合快速复制爆款视频，批量产出同类内容",
      "tasks.wizard.hint_baseline": "适合常规素材处理、批量混剪等通用需求",
      "lang.zh": "中文",
      hot_follow_new_pipeline_config: "加工流水线配置",
      hot_follow_new_target_lang: "目标语言",
      hot_follow_new_process_mode: "处理模式",
      hot_follow_new_mode_fast_title: "极速复刻",
      hot_follow_new_mode_fast_desc: "优先速度，快速产出",
      hot_follow_new_mode_smart_title: "智能仿写",
      hot_follow_new_mode_smart_desc: "更注重表达优化与适配",
      hot_follow_new_publish_account: "发布账号",
      hot_follow_new_task_title: "任务标题（可选）",
      hot_follow_workbench_tab_source: "源视频",
      hot_follow_workbench_tab_final: "最终成片",
      hot_follow_workbench_open_source: "打开源视频",
      hot_follow_workbench_open_final: "打开最终成片",
      hot_follow_workbench_wait_source: "等待源视频",
      hot_follow_workbench_subtitle_edit: "字幕编辑",
      hot_follow_workbench_subtitle_placeholder: "在此编辑 SRT 文本",
      hot_follow_workbench_source_label: "原文（Source）",
      hot_follow_workbench_target_label: "译文（Translated / Edited）",
      hot_follow_workbench_source_not_generated: "原文字幕尚未生成。",
      hot_follow_workbench_target_not_generated: "译文字幕尚未生成。",
      hot_follow_workbench_translation_cues_default: "翻译字幕条数：- / -",
      hot_follow_workbench_translation_cues_prefix: "翻译字幕条数",
      hot_follow_workbench_translation_mismatch: "翻译字幕条数不一致，请刷新或重跑字幕步骤。",
      hot_follow_workbench_subtitle_refresh: "刷新字幕",
      hot_follow_workbench_subtitle_save: "保存字幕",
      hot_follow_workbench_tts_preview: "试听",
      hot_follow_workbench_scene_pack_hint: "可选，未生成时不影响主流程",
      hot_follow_workbench_scene_pack_download: "下载 Scene Pack",
      hot_follow_publish_hint_title: "交付提示",
      hot_follow_publish_center_title: "发布中心",
      hot_follow_translation_qa_pass: "Translation QA: PASS",
      hot_follow_translation_qa_warn: "Translation QA: WARN",
      hot_follow_publish_copy_label: "发布文案",
      hot_follow_publish_copy_placeholder: "输入文案...",
      hot_follow_publish_backfill_title: "发布回填",
      hot_follow_compose_reason_ready: "可发布",
      hot_follow_compose_reason_final_missing: "尚未生成最终成片",
      hot_follow_compose_reason_in_progress: "合成中…",
      hot_follow_compose_reason_failed: "合成失败，可重试",
      hot_follow_compose_reason_missing_voice: "缺少配音",
      hot_follow_compose_reason_missing_raw: "缺少源视频",
      hot_follow_compose_running: "合成中…",
      hot_follow_delivery_group_final: "成片",
      hot_follow_delivery_group_pack: "剪辑包",
      hot_follow_delivery_group_subtitles: "字幕与脚本",
      hot_follow_delivery_group_audio: "音频素材",
      hot_follow_delivery_summary_prefix: "本次交付包含：",
      hot_follow_delivery_next_ready: "下一步：可直接发布成片或下载 pack 继续精修。",
      hot_follow_delivery_next_compose: "下一步：先回 Workbench 执行 Compose Final。",
      hot_follow_delivery_scene_pending_suffix: "（Scene Pack pending，不阻塞发布）",
      hot_follow_delivery_status_ready: "当前状态：✅ 可发布",
      hot_follow_delivery_status_prefix: "当前状态：⚠️",
      hot_follow_new_title: "热点跟拍 - 新建",
      hot_follow_new_hint_paste_link: "输入链接，生成热点跟拍任务",
      hot_follow_new_create_task: "创建任务",
      hot_follow_new_source_link: "来源链接",
      hot_follow_new_platform: "平台",
      hot_follow_new_link_preview: "链接预览",
      hot_follow_new_pipeline_config_badge: "配置",
      hot_follow_new_publish_account_default: "默认",
      hot_follow_new_create_run: "创建并运行",
      hot_follow_new_bgm_settings: "BGM 设置",
      hot_follow_new_bgm_mix_ratio: "BGM 混合比例 (0-1)",
      hot_follow_workbench_title: "热点跟拍 - 工作台",
      hot_follow_workbench_step_parse: "解析",
      hot_follow_workbench_step_subtitles: "字幕",
      hot_follow_workbench_step_dubbing: "配音",
      hot_follow_workbench_step_compose: "合成",
      hot_follow_workbench_confirm_voiceover: "确认配音用于合成就绪检查",
      hot_follow_workbench_tts_engine: "TTS 引擎",
      hot_follow_workbench_tts_voice: "TTS 音色",
      hot_follow_workbench_rerun_audio: "重新生成配音",
      hot_follow_workbench_bgm_upload: "BGM 上传",
      hot_follow_workbench_bgm_mix: "BGM 混音",
      hot_follow_workbench_audio_fit_cap: "语速上限",
      hot_follow_workbench_audio_fit_cap_normal: "正常 (1.25x)",
      hot_follow_workbench_audio_fit_cap_fast: "快速 (2.0x)",
      hot_follow_workbench_audio_fit_cap_hint: "正常更自然；快速适合长文本但可能偏赶",
      hot_follow_workbench_compose_title: "合成",
      hot_follow_workbench_composed_not_ready: "未就绪",
      hot_follow_workbench_overlay_target_subtitles: "叠加译文字幕",
      hot_follow_workbench_compose_confirm: "我确认配音与混音参数已就绪",
      hot_follow_workbench_compose_final: "合成最终视频",
      hot_follow_workbench_compose_disabled_hint: "合成不可用：请先确认就绪",
      hot_follow_workbench_reparse: "重新解析",
      hot_follow_workbench_resubtitles: "重新字幕",
      hot_follow_workbench_repack: "重新打包",
      hot_follow_workbench_scene_pack_optional: "分镜（可选）",
      hot_follow_workbench_scene_pack_generate: "生成 Scene Pack",
      hot_follow_workbench_deliverables: "交付物",
      hot_follow_delivery_title: "热点跟拍 - 交付中心",
      hot_follow_delivery_deliverables: "交付物",
      hot_follow_delivery_soft_subtitle_hint: "本次交付包含：Final / Pack / Subtitles / Audio / BGM…",
      hot_follow_delivery_publish_center: "发布中心",
      hot_follow_delivery_publish_feedback: "发布回填",
      hot_follow_delivery_publish_link: "发布链接",
      hot_follow_delivery_notes: "备注",
      hot_follow_delivery_submit: "回填发布",
      hot_follow_delivery_hashtags: "话题标签",
      hot_follow_delivery_hashtags_placeholder: "输入话题标签...",
      hot_follow_delivery_open_workbench: "打开工作台",
      common_buttons_download: "下载",
      common_status_pending: "pending",
      common_status_ready: "ready",
      common_loading: "...",
      common_ok: "OK",
      "lang.mm": "缅文",
      "lang.en": "English",
    },
    mm: {
      scn_apollo_avatar_title: "ApolloAvatar",
      scn_apollo_avatar_desc: "Avatar follow generation",
      apollo_avatar_duration: "ကြာချိန်",
      apollo_avatar_15s: "15 စက္ကန့်",
      apollo_avatar_30s: "30 စက္ကန့်",
      apollo_avatar_live_toggle: "Live (ကျသင့်)",
      apollo_avatar_live_hint: "Live ကိုဖွင့်လျှင် ကုန်ကျစရိတ်ရှိနိုင်သည်၊ မူလအနေဖြင့် demo သာ ပြပါမည်။",
      apollo_avatar_char_image: "ဇာတ်ကောင်ပုံ",
      apollo_avatar_prompt: "Prompt",
      apollo_avatar_ref_video: "ရည်ညွှန်းဗီဒီယို",
      apollo_avatar_create_task: "Task ဖန်တီးမည်",
      apollo_avatar_generate_demo: "Generate (Demo)",
      apollo_avatar_generate_live: "Generate (Live)",
      apollo_avatar_live_disabled_hint: "Live gate ကိုမဖွင့်ထားသေးပါ။",
      tab_digital_human: "Digital Human",
      tab_hot_follow: "Hot Follow",
      hot_follow_title: "Hot Follow",
      coming_soon: "Coming soon.",
      seed: "Seed",
      new_digital_human: "New Digital Human",
      "tasks.wizard.title": "Choose a Task Scenario",
      "tasks.wizard.subtitle": "Select the type of task to create. Each type has an optimized workflow.",
      "tasks.wizard.start": "Start",
      "tasks.scene.avatar.title": "Avatar IP",
      "tasks.scene.avatar.desc": "Recreate a real persona and follow a driving video. Supports lip-sync.",
      "tasks.scene.hot.title": "Hot Follow",
      "tasks.scene.hot.desc": "Deconstruct target videos for pixel-level replication. Auto-extract script & storyboard.",
      "tasks.scene.baseline.title": "Baseline Editing",
      "tasks.scene.baseline.desc": "General editing pipeline: dedupe, remix, basic dubbing.",
      "tasks.wizard.hint_title": "Tips",
      "tasks.wizard.hint_avatar": "Best for on-camera persona & brand spokesperson content",
      "tasks.wizard.hint_hot": "Best for quickly replicating viral formats at scale",
      "tasks.wizard.hint_baseline": "Best for general processing and batch remixing",
      "lang.zh": "တရုတ်",
      hot_follow_new_pipeline_config: "လုပ်ငန်းစဉ် ပြင်ဆင်မှု",
      hot_follow_new_target_lang: "ပစ်မှတ်ဘာသာစကား",
      hot_follow_new_process_mode: "လုပ်ဆောင်မှုမုဒ်",
      hot_follow_new_mode_fast_title: "အမြန်ကူးယူ",
      hot_follow_new_mode_fast_desc: "မြန်နှုန်းဦးစားပေး၊ အမြန်ထုတ်လုပ်",
      hot_follow_new_mode_smart_title: "ဥာဏ်ရည်မြှင့် ပြန်ရေး",
      hot_follow_new_mode_smart_desc: "အသုံးအနှုန်းကို ပိုမိုသင့်တော်အောင် ပြင်ဆင်",
      hot_follow_new_publish_account: "ဖြန့်ချိမည့် အကောင့်",
      hot_follow_new_task_title: "Task ခေါင်းစဉ် (ရွေးချယ်နိုင်)",
      hot_follow_workbench_tab_source: "မူရင်းဗီဒီယို",
      hot_follow_workbench_tab_final: "နောက်ဆုံးဗီဒီယို",
      hot_follow_workbench_open_source: "မူရင်းဗီဒီယိုဖွင့်မည်",
      hot_follow_workbench_open_final: "နောက်ဆုံးဗီဒီယိုဖွင့်မည်",
      hot_follow_workbench_wait_source: "မူရင်းဗီဒီယို စောင့်နေသည်",
      hot_follow_workbench_subtitle_edit: "စာတန်းပြင်ဆင်ရန်",
      hot_follow_workbench_subtitle_placeholder: "SRT စာသားကို ဒီနေရာတွင် ပြင်ဆင်ပါ",
      hot_follow_workbench_source_label: "မူရင်း (Source)",
      hot_follow_workbench_target_label: "ဘာသာပြန်/ပြင်ဆင်ထားသည် (Target)",
      hot_follow_workbench_source_not_generated: "မူရင်းစာတန်း မထုတ်လုပ်ရသေးပါ။",
      hot_follow_workbench_target_not_generated: "ဘာသာပြန်စာတန်း မထုတ်လုပ်ရသေးပါ။",
      hot_follow_workbench_translation_cues_default: "ဘာသာပြန်စာတန်း အရေအတွက်: - / -",
      hot_follow_workbench_translation_cues_prefix: "ဘာသာပြန်စာတန်း အရေအတွက်",
      hot_follow_workbench_translation_mismatch: "ဘာသာပြန်စာတန်း အရေအတွက် မကိုက်ညီပါ။ စာတန်းကို ပြန်လည်ရယူပါ သို့မဟုတ် subtitles step ကို ပြန်လုပ်ပါ။",
      hot_follow_workbench_subtitle_refresh: "စာတန်း ပြန်ယူ",
      hot_follow_workbench_subtitle_save: "စာတန်း သိမ်းမည်",
      hot_follow_workbench_tts_preview: "အသံနမူနာ",
      hot_follow_workbench_scene_pack_hint: "ရွေးချယ်နိုင်သောအရာဖြစ်ပြီး မထုတ်လုပ်ရသေးလည်း အဓိကလုပ်ငန်းစဉ်မထိခိုက်ပါ",
      hot_follow_workbench_scene_pack_download: "Scene Pack ဒေါင်းလုဒ်",
      hot_follow_publish_hint_title: "ပို့ဆောင်မှု အကြံပြုချက်",
      hot_follow_publish_center_title: "ဖြန့်ချိစင်တာ",
      hot_follow_translation_qa_pass: "Translation QA: PASS",
      hot_follow_translation_qa_warn: "Translation QA: WARN",
      hot_follow_publish_copy_label: "ဖြန့်ချိစာသား",
      hot_follow_publish_copy_placeholder: "စာသားထည့်ပါ...",
      hot_follow_publish_backfill_title: "ဖြန့်ချိပြန်ဖြည့်ခြင်း",
      hot_follow_compose_reason_ready: "ဖြန့်ချိရန် အသင့်ဖြစ်ပါသည်",
      hot_follow_compose_reason_final_missing: "နောက်ဆုံးဗီဒီယို မရှိသေးပါ",
      hot_follow_compose_reason_in_progress: "ပေါင်းစည်းနေသည်…",
      hot_follow_compose_reason_failed: "ပေါင်းစည်းမှု မအောင်မြင်ပါ၊ ပြန်ကြိုးစားနိုင်သည်",
      hot_follow_compose_reason_missing_voice: "အသံဖိုင် မရှိပါ",
      hot_follow_compose_reason_missing_raw: "မူရင်းဗီဒီယို မရှိပါ",
      hot_follow_compose_running: "ပေါင်းစည်းနေသည်…",
      hot_follow_delivery_group_final: "နောက်ဆုံးဗီဒီယို",
      hot_follow_delivery_group_pack: "Pack ဖိုင်များ",
      hot_follow_delivery_group_subtitles: "စာတန်းနှင့် စာသား",
      hot_follow_delivery_group_audio: "အသံဖိုင်များ",
      hot_follow_delivery_summary_prefix: "ယခု ပို့ဆောင်မှုတွင် ပါဝင်သည် - ",
      hot_follow_delivery_next_ready: "နောက်တစ်ဆင့် - နောက်ဆုံးဗီဒီယိုကို တိုက်ရိုက်ဖြန့်ချိနိုင်သည် သို့မဟုတ် pack ကို ဒေါင်းလုဒ်ယူပြီး ဆက်လက်ပြင်ဆင်နိုင်သည်။",
      hot_follow_delivery_next_compose: "နောက်တစ်ဆင့် - Workbench သို့ ပြန်သွားပြီး Compose Final ကို လုပ်ပါ။",
      hot_follow_delivery_scene_pending_suffix: " (Scene Pack pending, ဖြန့်ချိမှုကို မတားဆီးပါ)",
      hot_follow_delivery_status_ready: "လက်ရှိအခြေအနေ - ✅ ဖြန့်ချိနိုင်သည်",
      hot_follow_delivery_status_prefix: "လက်ရှိအခြေအနေ - ⚠️",
      hot_follow_new_title: "Hot Follow - New",
      hot_follow_new_hint_paste_link: "Paste a link to create a hot follow task",
      hot_follow_new_create_task: "Create Task",
      hot_follow_new_source_link: "Source link",
      hot_follow_new_platform: "Platform",
      hot_follow_new_link_preview: "Link Preview",
      hot_follow_new_pipeline_config_badge: "Config",
      hot_follow_new_publish_account_default: "Default",
      hot_follow_new_create_run: "Create & Run",
      hot_follow_new_bgm_settings: "BGM Settings",
      hot_follow_new_bgm_mix_ratio: "BGM mix ratio (0-1)",
      hot_follow_workbench_title: "Hot Follow - Workbench",
      hot_follow_workbench_step_parse: "Parse",
      hot_follow_workbench_step_subtitles: "Subtitles",
      hot_follow_workbench_step_dubbing: "Dubbing",
      hot_follow_workbench_step_compose: "Compose",
      hot_follow_workbench_confirm_voiceover: "Confirm voiceover for compose readiness",
      hot_follow_workbench_tts_engine: "TTS Engine",
      hot_follow_workbench_tts_voice: "TTS Voice",
      hot_follow_workbench_rerun_audio: "Re-Run Audio",
      hot_follow_workbench_bgm_upload: "BGM Upload",
      hot_follow_workbench_bgm_mix: "BGM Mix",
      hot_follow_workbench_audio_fit_cap: "Audio Fit Speed Cap",
      hot_follow_workbench_audio_fit_cap_normal: "Normal (1.25x)",
      hot_follow_workbench_audio_fit_cap_fast: "Fast (2.0x)",
      hot_follow_workbench_audio_fit_cap_hint: "Normal preserves naturalness; fast may sound rushed",
      hot_follow_workbench_compose_title: "Compose",
      hot_follow_workbench_composed_not_ready: "Not Ready",
      hot_follow_workbench_overlay_target_subtitles: "Overlay target subtitles",
      hot_follow_workbench_compose_confirm: "I confirm voiceover and mix settings are ready",
      hot_follow_workbench_compose_final: "Compose Final",
      hot_follow_workbench_compose_disabled_hint: "Compose disabled: check confirmation first",
      hot_follow_workbench_reparse: "Re-Parse",
      hot_follow_workbench_resubtitles: "Re-Subtitles",
      hot_follow_workbench_repack: "Re-Pack",
      hot_follow_workbench_scene_pack_optional: "Scene Pack (optional)",
      hot_follow_workbench_scene_pack_generate: "Generate Scene Pack",
      hot_follow_workbench_deliverables: "Deliverables",
      hot_follow_delivery_title: "Hot Follow - Delivery Center",
      hot_follow_delivery_deliverables: "Deliverables",
      hot_follow_delivery_soft_subtitle_hint: "This delivery includes: Final / Pack / Subtitles / Audio / BGM…",
      hot_follow_delivery_publish_center: "Publish Center",
      hot_follow_delivery_publish_feedback: "Publish Feedback",
      hot_follow_delivery_publish_link: "Publish link",
      hot_follow_delivery_notes: "Notes",
      hot_follow_delivery_submit: "Submit",
      hot_follow_delivery_hashtags: "Hashtags",
      hot_follow_delivery_hashtags_placeholder: "Enter hashtags...",
      hot_follow_delivery_open_workbench: "Open Workbench",
      common_buttons_download: "Download",
      common_status_pending: "pending",
      common_status_ready: "ready",
      common_loading: "...",
      common_ok: "OK",
      "lang.mm": "မြန်မာ",
      "lang.en": "English",
    },
    en: {
      hot_follow_new_title: "Hot Follow - New",
      hot_follow_new_hint_paste_link: "Paste a link to create a hot follow task",
      hot_follow_new_create_task: "Create Task",
      hot_follow_new_source_link: "Source link",
      hot_follow_new_platform: "Platform",
      hot_follow_new_link_preview: "Link Preview",
      hot_follow_new_pipeline_config: "Pipeline Config",
      hot_follow_new_pipeline_config_badge: "Config",
      hot_follow_new_target_lang: "Target language",
      hot_follow_new_process_mode: "Process mode",
      hot_follow_new_mode_fast_title: "Fast",
      hot_follow_new_mode_fast_desc: "Prioritize speed, faster output",
      hot_follow_new_mode_smart_title: "Intelligent",
      hot_follow_new_mode_smart_desc: "Better rewriting & adaptation",
      hot_follow_new_publish_account: "Publish account",
      hot_follow_new_publish_account_default: "Default",
      hot_follow_new_task_title: "Task title (optional)",
      hot_follow_new_create_run: "Create & Run",
      hot_follow_new_bgm_settings: "BGM Settings",
      hot_follow_new_bgm_replace: "Replace audio",
      hot_follow_new_bgm_keep: "Keep original",
      hot_follow_new_bgm_mute: "Mute",
      hot_follow_new_bgm_mix_ratio: "BGM mix ratio (0-1)",
      hot_follow_workbench_title: "Hot Follow - Workbench",
      hot_follow_workbench_pipeline_title: "Processing Pipeline",
      hot_follow_workbench_step_parse: "Parse",
      hot_follow_workbench_step_subtitles: "Subtitles",
      hot_follow_workbench_step_dubbing: "Dubbing",
      hot_follow_workbench_step_compose: "Compose",
      hot_follow_workbench_confirm_voiceover: "Confirm voiceover for compose readiness",
      hot_follow_workbench_tts_engine: "TTS Engine",
      hot_follow_workbench_tts_voice: "TTS Voice",
      hot_follow_workbench_rerun_audio: "Re-Run Audio",
      hot_follow_workbench_bgm_upload: "BGM Upload",
      hot_follow_workbench_bgm_mix: "BGM Mix",
      hot_follow_workbench_audio_fit_cap: "Audio Fit Speed Cap",
      hot_follow_workbench_audio_fit_cap_normal: "Normal (1.25x)",
      hot_follow_workbench_audio_fit_cap_fast: "Fast (2.0x)",
      hot_follow_workbench_audio_fit_cap_hint: "Normal preserves naturalness; fast may sound rushed",
      hot_follow_workbench_compose_title: "Compose",
      hot_follow_workbench_composed_not_ready: "Not Ready",
      hot_follow_workbench_overlay_target_subtitles: "Overlay target subtitles",
      hot_follow_workbench_compose_confirm: "I confirm voiceover and mix settings are ready",
      hot_follow_workbench_compose_final: "Compose Final",
      hot_follow_workbench_compose_disabled_hint: "Compose disabled: check confirmation first",
      hot_follow_workbench_reparse: "Re-Parse",
      hot_follow_workbench_resubtitles: "Re-Subtitles",
      hot_follow_workbench_repack: "Re-Pack",
      hot_follow_workbench_input_config: "INPUT CONFIG",
      hot_follow_workbench_subtitle_edit: "Subtitle Edit",
      hot_follow_workbench_source_label: "Source",
      hot_follow_workbench_target_label: "Target",
      hot_follow_workbench_subtitle_placeholder: "Edit SRT text here",
      hot_follow_workbench_tab_source: "Source",
      hot_follow_workbench_tab_final: "Final",
      hot_follow_workbench_open_source: "Open source",
      hot_follow_workbench_open_final: "Open final",
      hot_follow_workbench_scene_pack_optional: "Scene Pack (optional)",
      hot_follow_workbench_scene_pack_generate: "Generate Scene Pack",
      hot_follow_workbench_scene_pack_download: "Download Scene Pack",
      hot_follow_workbench_deliverables: "Deliverables",
      hot_follow_delivery_title: "Hot Follow - Delivery Center",
      hot_follow_delivery_deliverables: "Deliverables",
      hot_follow_delivery_soft_subtitle_hint: "This delivery includes: Final / Pack / Subtitles / Audio / BGM…",
      hot_follow_delivery_publish_center: "Publish Center",
      hot_follow_delivery_publish_feedback: "Publish Feedback",
      hot_follow_delivery_publish_link: "Publish link",
      hot_follow_delivery_notes: "Notes",
      hot_follow_delivery_submit: "Submit",
      hot_follow_delivery_hashtags: "Hashtags",
      hot_follow_delivery_hashtags_placeholder: "Enter hashtags...",
      hot_follow_delivery_open_workbench: "Open Workbench",
      common_buttons_download: "Download",
      common_status_pending: "pending",
      common_status_ready: "ready",
      common_loading: "...",
      common_ok: "OK",
      "lang.zh": "Chinese",
      "lang.mm": "Burmese",
      "lang.en": "English",
    },
  };

  CLIENT_DICT.en = CLIENT_DICT.en || {};
  Object.assign(CLIENT_DICT.zh, {
    hot_follow_new_hint: "输入链接，生成热点跟拍任务",
    hot_follow_new_source_link_ph: "粘贴来源链接 (Douyin/XHS/TK/FB)",
    hot_follow_new_platform_auto: "自动",
    hot_follow_new_task_title_ph: "可选标题",
    hot_follow_new_create_and_run: "创建并运行",
    hot_follow_workbench_track_hint: "任务进度与步骤控制",
    hot_follow_workbench_parse: "解析",
    hot_follow_workbench_subtitles: "字幕",
    hot_follow_workbench_dubbing: "配音",
    hot_follow_workbench_compose_hint: "合成从未运行",
    hot_follow_delivery_hint_title: "交付提示",
    hot_follow_publish_center: "发布中心",
    hot_follow_publish_feedback: "发布回填",
    hot_follow_publish_link: "发布链接",
    hot_follow_publish_notes: "备注",
    hot_follow_publish_submit: "回填发布",
    hot_follow_publish_hashtags: "话题标签",
    hot_follow_publish_hashtags_placeholder: "输入标签，空格分隔，例如 #hot #trend",
    hot_follow_scene_pack_title: "分镜（可选）",
    hot_follow_scene_pack_desc: "可选，未生成时不影响主流程",
    hot_follow_scene_pack_generate: "生成 Scene Pack",
    hot_follow_scene_pack_download: "下载 Scene Pack",
    hot_follow_scenes_title: "场景切片",
    hot_follow_scenes_desc: "用于运营复用的场景切片。",
    hot_follow_scenes_generate: "生成场景切片",
    hot_follow_scenes_download: "下载 Scenes.zip",
    hot_follow_scene_status_pending: "未就绪",
    hot_follow_scene_status_done: "已就绪",
  });
  Object.assign(CLIENT_DICT.mm, {
    hot_follow_new_title: "Hot Follow - အသစ်",
    hot_follow_new_hint: "လင့်ခ်ထည့်၍ Hot Follow တာဝန်ဖန်တီးပါ",
    hot_follow_new_create_task: "တာဝန်ဖန်တီး",
    hot_follow_new_source_link: "မူရင်းလင့်ခ်",
    hot_follow_new_source_link_ph: "လင့်ခ်ကူးထည့်ပါ (Douyin/XHS/TK/FB)",
    hot_follow_new_platform: "ပလက်ဖောင်း",
    hot_follow_new_platform_auto: "အလိုအလျောက်",
    hot_follow_new_link_preview: "လင့်ခ်အစမ်းကြည့်",
    hot_follow_new_bgm_settings: "BGM သတ်မှတ်ချက်",
    hot_follow_new_bgm_replace: "မူရင်းအသံအစားထိုး",
    hot_follow_new_bgm_keep: "မူရင်းအသံထား",
    hot_follow_new_bgm_mute: "အသံပိတ်",
    hot_follow_new_bgm_mix_ratio: "BGM ပေါင်းစပ်အချိုး (0-1)",
    hot_follow_new_pipeline_config: "လုပ်ငန်းစဉ် ချိန်ညှိမှု",
    hot_follow_new_pipeline_config_badge: "ချိန်ညှိ",
    hot_follow_new_target_lang: "ပစ်မှတ်ဘာသာ",
    hot_follow_new_process_mode: "လုပ်ဆောင်မုဒ်",
    hot_follow_new_mode_fast_title: "မြန်ဆန်ကူးယူ",
    hot_follow_new_mode_fast_desc: "မြန်နှုန်းဦးစား၊ အမြန်ထုတ်လုပ်",
    hot_follow_new_mode_smart_title: "ဉာဏ်ရည်ကူးရေး",
    hot_follow_new_mode_smart_desc: "စာသားတိုးတက်ရေးနှင့် သင့်တော်မှု ဦးစား",
    hot_follow_new_publish_account: "ထုတ်ဝေ အကောင့်",
    hot_follow_new_publish_account_default: "မူလ",
    hot_follow_new_task_title: "ခေါင်းစဉ် (ရွေးချယ်နိုင်)",
    hot_follow_new_task_title_ph: "ခေါင်းစဉ်ထည့်နိုင်",
    hot_follow_new_create_and_run: "ဖန်တီးပြီး လုပ်ဆောင်",
    hot_follow_workbench_title: "Hot Follow - Workbench",
    hot_follow_workbench_track_hint: "လုပ်ငန်းတိုးတက်မှုနှင့် ထိန်းချုပ်မှု",
    hot_follow_workbench_tab_source: "မူရင်းဗီဒီယို",
    hot_follow_workbench_tab_final: "နောက်ဆုံးဗီဒီယို",
    hot_follow_workbench_open_source: "မူရင်းဖွင့်",
    hot_follow_workbench_open_final: "နောက်ဆုံးဖွင့်",
    hot_follow_workbench_pipeline_title: "လုပ်ငန်းစဉ်",
    hot_follow_workbench_parse: "ခွဲခြမ်း",
    hot_follow_workbench_subtitles: "စာတန်း",
    hot_follow_workbench_dubbing: "အသံထည့်",
    hot_follow_workbench_confirm_voiceover: "အသံကို အတည်ပြုပြီး ပေါင်းစပ်ရန်",
    hot_follow_workbench_tts_engine: "TTS အင်ဂျင်",
    hot_follow_workbench_tts_voice: "အသံရွေးချယ်",
    hot_follow_workbench_tts_preview: "စမ်းနားထောင်",
    hot_follow_workbench_rerun_audio: "အသံပြန်လုပ်",
    hot_follow_workbench_bgm_upload: "BGM တင်",
    hot_follow_workbench_bgm_mix: "BGM ပေါင်းစပ်",
    hot_follow_workbench_audio_fit_cap: "အသံညှိနှိုင်း အမြန်နှုန်းကန့်သတ်",
    hot_follow_workbench_audio_fit_cap_normal: "ပုံမှန် (1.25x)",
    hot_follow_workbench_audio_fit_cap_fast: "မြန် (2.0x)",
    hot_follow_workbench_audio_fit_cap_hint: "Normal သဘာဝ၊ Fast ရှည်စာကို တိုဗီဒီယိုနှင့် ကိုက်ညီစေသော်လည်း မြန်နိုင်",
    hot_follow_workbench_compose_title: "ပေါင်းစပ်",
    hot_follow_workbench_composed_not_ready: "မအဆင်သင့်",
    hot_follow_workbench_compose_hint: "ပေါင်းစပ်မလုပ်ရသေး",
    hot_follow_workbench_overlay_target_subtitles: "ဘာသာပြန်စာတန်း ထပ်တင်",
    hot_follow_workbench_compose_confirm: "အသံ/ပေါင်းစပ် စနစ်များ အဆင်သင့်",
    hot_follow_workbench_compose_final: "နောက်ဆုံးပေါင်းစပ်",
    hot_follow_workbench_reparse: "ပြန်ခွဲခြမ်း",
    hot_follow_workbench_resubtitles: "စာတန်းပြန်လုပ်",
    hot_follow_workbench_repack: "ပြန်ထုပ်",
    hot_follow_workbench_input_config: "ထည့်သွင်းချက်",
    hot_follow_workbench_subtitle_edit: "စာတန်းတည်းဖြတ်",
    hot_follow_workbench_source_label: "မူရင်း (Source)",
    hot_follow_workbench_target_label: "ဘာသာပြန် (Target)",
    hot_follow_workbench_subtitle_placeholder: "SRT စာတန်းကို ဒီမှာ ပြ/တည်းဖြတ်",
    hot_follow_delivery_title: "Hot Follow - Delivery",
    hot_follow_delivery_hint_title: "ပို့ဆောင်ညွှန်ကြား",
    hot_follow_delivery_soft_subtitle_hint: "ပို့ဆောင်ပါဝင်ချက်… နောက်တစ်ဆင့် Workbench မှ Compose Final လုပ်ပါ",
    hot_follow_publish_center: "ထုတ်ဝေစင်တာ",
    hot_follow_publish_feedback: "ထုတ်ဝေပြန်ထည့်",
    hot_follow_publish_link: "ထုတ်ဝေလင့်ခ်",
    hot_follow_publish_notes: "မှတ်ချက်",
    hot_follow_publish_submit: "ပြန်ထည့်တင်",
    hot_follow_publish_hashtags: "ဟတ်ရှ်တဂ်",
    hot_follow_publish_hashtags_placeholder: "ဟတ်ရှ်တဂ်ထည့်ပါ…",
    hot_follow_delivery_open_workbench: "Workbench ဖွင့်",
    hot_follow_scene_pack_title: "စီကွက် (ရွေးချယ်နိုင်)",
    hot_follow_scene_pack_desc: "မဖြစ်လည်း အဓိကလုပ်ငန်းစဉ် မထိခိုက်",
    hot_follow_scene_pack_generate: "Scene Pack ဖန်တီး",
    hot_follow_scene_pack_download: "Scene Pack ဒေါင်း",
    hot_follow_scenes_title: "Scene ခွဲထုတ်",
    hot_follow_scenes_desc: "လုပ်ငန်းပြန်သုံးရန် Scene ခွဲထုတ်",
    hot_follow_scenes_generate: "Scene ခွဲထုတ်ဖန်တီး",
    hot_follow_scenes_download: "Scenes.zip ဒေါင်း",
    hot_follow_scene_status_pending: "မအဆင်သင့်",
    hot_follow_scene_status_done: "အဆင်သင့်",
  });
  Object.assign(CLIENT_DICT.en, {
    hot_follow_new_title: "Hot Follow - New",
    hot_follow_new_hint: "Paste a link to create a hot follow task",
    hot_follow_new_create_task: "Create Task",
    hot_follow_new_source_link: "Source Link",
    hot_follow_new_source_link_ph: "Paste link (Douyin/XHS/TK/FB)",
    hot_follow_new_platform: "Platform",
    hot_follow_new_platform_auto: "Auto",
    hot_follow_new_link_preview: "Link Preview",
    hot_follow_new_bgm_settings: "BGM Settings",
    hot_follow_new_bgm_replace: "Replace audio",
    hot_follow_new_bgm_keep: "Keep original",
    hot_follow_new_bgm_mute: "Mute",
    hot_follow_new_bgm_mix_ratio: "BGM mix ratio (0-1)",
    hot_follow_new_pipeline_config: "Pipeline Config",
    hot_follow_new_pipeline_config_badge: "Config",
    hot_follow_new_target_lang: "Target language",
    hot_follow_new_process_mode: "Process mode",
    hot_follow_new_mode_fast_title: "Fast Clone",
    hot_follow_new_mode_fast_desc: "Prioritize speed, output fast",
    hot_follow_new_mode_smart_title: "Smart Rewrite",
    hot_follow_new_mode_smart_desc: "Optimize phrasing and adaptation",
    hot_follow_new_publish_account: "Publish account",
    hot_follow_new_publish_account_default: "Default",
    hot_follow_new_task_title: "Title (optional)",
    hot_follow_new_task_title_ph: "Optional title",
    hot_follow_new_create_and_run: "Create & Run",
    hot_follow_workbench_title: "Hot Follow - Workbench",
    hot_follow_workbench_track_hint: "Track progress and control steps",
    hot_follow_workbench_tab_source: "Source",
    hot_follow_workbench_tab_final: "Final",
    hot_follow_workbench_open_source: "Open source",
    hot_follow_workbench_open_final: "Open final",
    hot_follow_workbench_pipeline_title: "Processing Pipeline",
    hot_follow_workbench_parse: "Parse",
    hot_follow_workbench_subtitles: "Subtitles",
    hot_follow_workbench_dubbing: "Dubbing",
    hot_follow_workbench_confirm_voiceover: "Confirm voiceover for compose readiness",
    hot_follow_workbench_tts_engine: "TTS Engine",
    hot_follow_workbench_tts_voice: "TTS Voice",
    hot_follow_workbench_tts_preview: "Preview",
    hot_follow_workbench_rerun_audio: "Re-Run Audio",
    hot_follow_workbench_bgm_upload: "BGM Upload",
    hot_follow_workbench_bgm_mix: "BGM Mix",
    hot_follow_workbench_audio_fit_cap: "Audio fit speed cap",
    hot_follow_workbench_audio_fit_cap_normal: "Normal (1.25x)",
    hot_follow_workbench_audio_fit_cap_fast: "Fast (2.0x)",
    hot_follow_workbench_audio_fit_cap_hint: "Normal preserves naturalness; Fast may sound rushed",
    hot_follow_workbench_compose_title: "Compose",
    hot_follow_workbench_composed_not_ready: "Not Ready",
    hot_follow_workbench_compose_hint: "Compose never run",
    hot_follow_workbench_overlay_target_subtitles: "Overlay target subtitles",
    hot_follow_workbench_compose_confirm: "I confirm voiceover and mix settings are ready",
    hot_follow_workbench_compose_final: "Compose Final",
    hot_follow_workbench_reparse: "Re-Parse",
    hot_follow_workbench_resubtitles: "Re-Subtitles",
    hot_follow_workbench_repack: "Re-Pack",
    hot_follow_workbench_input_config: "Input Config",
    hot_follow_workbench_subtitle_edit: "Subtitle Edit",
    hot_follow_workbench_source_label: "Source",
    hot_follow_workbench_target_label: "Target",
    hot_follow_workbench_subtitle_placeholder: "SRT will appear here",
    hot_follow_delivery_title: "Hot Follow - Delivery",
    hot_follow_delivery_hint_title: "Delivery hints",
    hot_follow_delivery_soft_subtitle_hint: "This delivery includes… Next: run Compose Final in Workbench",
    hot_follow_publish_center: "Publish Center",
    hot_follow_publish_feedback: "Publish Feedback",
    hot_follow_publish_link: "Publish link",
    hot_follow_publish_notes: "Notes",
    hot_follow_publish_submit: "Submit",
    hot_follow_publish_hashtags: "Hashtags",
    hot_follow_publish_hashtags_placeholder: "Enter hashtags…",
    hot_follow_delivery_open_workbench: "Open workbench",
    hot_follow_scene_pack_title: "Scene Pack (Optional)",
    hot_follow_scene_pack_desc: "Optional; does not block main flow",
    hot_follow_scene_pack_generate: "Generate Scene Pack",
    hot_follow_scene_pack_download: "Download Scene Pack",
    hot_follow_scenes_title: "Scene Slices",
    hot_follow_scenes_desc: "Reusable scene slices for ops",
    hot_follow_scenes_generate: "Generate Scenes",
    hot_follow_scenes_download: "Download Scenes.zip",
    hot_follow_scene_status_pending: "Pending",
    hot_follow_scene_status_done: "Done",
  });

  function getPayload() {
    return window.__I18N__ || { locale: "zh", supported: ["zh", "mm", "en"], dict: { zh: {}, mm: {}, en: {} } };
  }

  function getSupported() {
    const payload = getPayload();
    const supported = payload.supported || ["zh", "mm", "en"];
    return ["zh", "mm", "en"].filter((x) => supported.includes(x));
  }

  function normalizeLocale(locale) {
    const loc = String(locale || "").toLowerCase();
    if (loc === "zh" || loc === "mm" || loc === "en") return loc;
    return "en";
  }

  function getQueryLocale() {
    const qs = new URLSearchParams(window.location.search || "");
    return (qs.get(PARAM_NAME) || "").toLowerCase();
  }

  function getCookieLocale() {
    const m = document.cookie.match(new RegExp("(?:^|; )" + COOKIE_NAME + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : "";
  }

  function setCookie(locale) {
    const maxAge = 60 * 60 * 24 * 365;
    document.cookie = `${COOKIE_NAME}=${encodeURIComponent(locale)}; path=/; max-age=${maxAge}`;
  }

  function setQueryLocale(locale) {
    const url = new URL(window.location.href);
    url.searchParams.set(PARAM_NAME, locale);
    window.location.href = url.toString();
  }

  function resolveLocale() {
    const payload = getPayload();
    const supported = getSupported();
    const queryLocale = normalizeLocale(getQueryLocale());
    if (supported.includes(queryLocale)) return queryLocale;
    const cookieLocale = normalizeLocale(getCookieLocale());
    if (supported.includes(cookieLocale)) return cookieLocale;
    const payloadLocale = normalizeLocale(payload.locale);
    if (supported.includes(payloadLocale)) return payloadLocale;
    return "en";
  }

  function getFallbacks() {
    const payload = getPayload();
    return payload.fallbacks || {
      mm: ["mm", "en", "zh"],
      zh: ["zh", "en"],
      en: ["en", "zh"],
    };
  }

  function t(key, vars) {
    const payload = getPayload();
    const locale = resolveLocale();
    const dict = payload.dict || {};
    const fallbacks = getFallbacks();
    const chain = fallbacks[locale] || [locale, "en", "zh"];
    let text;
    for (const loc of chain) {
      const table = dict[loc] || {};
      if (table[key]) {
        text = table[key];
        break;
      }
      const clientTable = CLIENT_DICT[loc] || {};
      if (clientTable[key]) {
        text = clientTable[key];
        break;
      }
    }
    if (!text) {
      console.warn("[i18n-miss]", locale, key);
      text = (CLIENT_DICT.en && CLIENT_DICT.en[key]) || key;
    }
    if (vars && typeof text === "string") {
      Object.keys(vars).forEach((k) => {
        text = text.replace(new RegExp(`\\{${k}\\}`, "g"), String(vars[k]));
      });
    }
    return text;
  }

  function _translateElements(locale, root) {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      el.textContent = t(key);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      el.setAttribute("placeholder", t(key));
    });
    root.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      el.setAttribute("title", t(key));
    });
  }

  function applyLocale(locale, rootEl) {
    const root = rootEl || document;
    if (!locale) locale = resolveLocale();
    if (root === document || root === document.documentElement || root === document.body) {
      document.documentElement.setAttribute("data-locale", locale);
    }
    if (root.nodeType === 1) {
      if (root.matches("[data-i18n]")) root.textContent = t(root.getAttribute("data-i18n"));
      if (root.matches("[data-i18n-placeholder]")) root.setAttribute("placeholder", t(root.getAttribute("data-i18n-placeholder")));
      if (root.matches("[data-i18n-title]")) root.setAttribute("title", t(root.getAttribute("data-i18n-title")));
    }
    _translateElements(locale, root);
  }

  let observer = null;
  let observerTimer = null;
  const pendingRoots = new Set();

  function _queueRefreshRoot(node) {
    if (!node || !(node.nodeType === 1 || node.nodeType === 9)) return;
    pendingRoots.add(node);
    if (observerTimer) return;
    observerTimer = setTimeout(() => {
      observerTimer = null;
      const locale = resolveLocale();
      pendingRoots.forEach((root) => applyLocale(locale, root));
      pendingRoots.clear();
    }, 50);
  }

  function _containsI18nAttrs(node) {
    if (!node || node.nodeType !== 1) return false;
    if (
      node.hasAttribute("data-i18n") ||
      node.hasAttribute("data-i18n-placeholder") ||
      node.hasAttribute("data-i18n-title") ||
      node.hasAttribute("data-lang-tab")
    ) {
      return true;
    }
    return Boolean(
      node.querySelector("[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-lang-tab]")
    );
  }

  // Observe async-rendered DOM blocks and re-apply locale with debounce.
  function watchDomI18n() {
    if (observer || typeof MutationObserver === "undefined" || !document.body) return;
    observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type !== "childList" || !m.addedNodes || !m.addedNodes.length) continue;
        for (const n of m.addedNodes) {
          if (_containsI18nAttrs(n)) _queueRefreshRoot(n);
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function boot() {
    const locale = resolveLocale();
    applyLocale(locale, document);
    watchDomI18n();
    document.querySelectorAll("[data-lang-tab]").forEach((el) => {
      el.classList.toggle("active", el.getAttribute("data-lang-tab") === locale);
      el.addEventListener("click", (e) => {
        e.preventDefault();
        const target = el.getAttribute("data-lang-tab");
        if (!target) return;
        setCookie(target);
        applyLocale(target, document);
        setQueryLocale(target);
      });
    });
  }

  function readLocale() {
    return resolveLocale();
  }

  window.__V185_I18N__ = { t, readLocale, applyLocale, watchDomI18n };
  // Page scripts can force a full i18n pass after dynamic rendering.
  window.__I18N_REAPPLY__ = () => window.__V185_I18N__.applyLocale(window.__V185_I18N__.readLocale());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
