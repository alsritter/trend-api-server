// 状态映射
export const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_validation: { label: "待验证", color: "orange" },
  validated: { label: "已验证", color: "green" },
  rejected: { label: "已拒绝（初筛）", color: "red" },
  second_stage_rejected: { label: "已拒绝（第二阶段）", color: "volcano" },
  crawling: { label: "爬取中", color: "blue" },
  crawled: { label: "已爬取", color: "cyan" },
  analyzing: { label: "分析中", color: "purple" },
  analyzed: { label: "已分析", color: "geekblue" },
  archived: { label: "已归档", color: "default" },
  outdated: { label: "已过时", color: "magenta" }
};

// 平台映射（显示用）
export const PLATFORM_MAP: Record<string, string> = {
  小红书: "小红书",
  抖音: "抖音",
  哔哩哔哩: "哔哩哔哩",
  微博: "微博",
  快手: "快手",
  贴吧: "贴吧",
  知乎: "知乎"
};

// 平台名称到代码的映射（API调用用）
export const PLATFORM_NAME_TO_CODE: Record<string, string> = {
  "小红书": "xhs",
  "抖音": "dy",
  "哔哩哔哩": "bili",
  "微博": "wb",
  "快手": "ks",
  "贴吧": "tieba",
  "知乎": "zhihu",
  // 兼容已经是代码的情况
  "xhs": "xhs",
  "dy": "dy",
  "bili": "bili",
  "wb": "wb",
  "ks": "ks",
  "tieba": "tieba",
  "zhihu": "zhihu"
};
