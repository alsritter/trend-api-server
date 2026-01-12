import type { HotspotDetail, HotspotStatus } from "@/types/api";

// 状态标签映射
export const STATUS_MAP: Record<
  HotspotStatus,
  { label: string; color: string }
> = {
  pending_validation: { label: "待验证", color: "default" },
  validated: { label: "已验证", color: "blue" },
  rejected: { label: "已过滤", color: "red" },
  second_stage_rejected: { label: "二次过滤", color: "red" },
  crawling: { label: "爬取中", color: "processing" },
  crawled: { label: "已爬取", color: "cyan" },
  analyzing: { label: "分析中", color: "purple" },
  analyzed: { label: "已分析", color: "green" },
  archived: { label: "已归档", color: "default" },
  outdated: {
    label: "已过时",
    color: "default"
  }
};

export interface HotspotTableColumnsProps {
  onViewDetail: (record: HotspotDetail) => void;
  onDelete: (hotspotId: number) => void;
  onViewCluster?: (clusterId: number) => void;
  isDeleting: boolean;
}
