// 状态映射
export const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_validation: { label: "待验证", color: "orange" },
  validated: { label: "已验证", color: "green" },
  rejected: { label: "已拒绝", color: "red" },
  crawling: { label: "爬取中", color: "blue" },
  crawled: { label: "已爬取", color: "cyan" },
  analyzing: { label: "分析中", color: "purple" },
  analyzed: { label: "已分析", color: "geekblue" },
  archived: { label: "已归档", color: "default" },
  outdated: { label: "已过时", color: "volcano" }
};

// 平台映射
export const PLATFORM_MAP: Record<string, string> = {
  小红书: "小红书",
  抖音: "抖音",
  哔哩哔哩: "哔哩哔哩",
  微博: "微博",
  快手: "快手",
  贴吧: "贴吧",
  知乎: "知乎"
};
