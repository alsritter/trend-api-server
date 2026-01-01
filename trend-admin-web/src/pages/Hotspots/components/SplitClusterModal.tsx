import { Modal, Checkbox, message, Space } from "antd";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { clustersApi } from "@/api/clusters";
import type { HotspotDetail, SplitClusterResponse } from "@/types/api";

interface SplitClusterModalProps {
  visible: boolean;
  clusterId: number;
  clusterName: string;
  hotspots: HotspotDetail[];
  onClose: () => void;
}

export function SplitClusterModal({
  visible,
  clusterId,
  clusterName,
  hotspots,
  onClose,
}: SplitClusterModalProps) {
  const queryClient = useQueryClient();
  const [selectedHotspots, setSelectedHotspots] = useState<number[]>([]);

  const splitMutation = useMutation({
    mutationFn: ({ clusterId, hotspotIds }: { clusterId: number; hotspotIds: number[] }) =>
      clustersApi.split(clusterId, { hotspot_ids: hotspotIds }),
    onSuccess: (data: SplitClusterResponse) => {
      message.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
      queryClient.invalidateQueries({ queryKey: ["hotspots"] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(`拆分失败: ${error.message}`);
    },
  });

  const handleClose = () => {
    setSelectedHotspots([]);
    onClose();
  };

  const handleOk = () => {
    if (selectedHotspots.length === 0) {
      message.warning("请至少选择一个热点");
      return;
    }

    if (selectedHotspots.length === hotspots.length) {
      message.warning("不能移出所有热点，这会删除整个聚簇");
      return;
    }

    splitMutation.mutate({ clusterId, hotspotIds: selectedHotspots });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedHotspots(hotspots.map((h) => h.id));
    } else {
      setSelectedHotspots([]);
    }
  };

  const isAllSelected = selectedHotspots.length === hotspots.length && hotspots.length > 0;
  const isIndeterminate = selectedHotspots.length > 0 && selectedHotspots.length < hotspots.length;

  return (
    <Modal
      title={`拆分聚簇: ${clusterName}`}
      open={visible}
      onOk={handleOk}
      onCancel={handleClose}
      okText="拆分"
      cancelText="取消"
      confirmLoading={splitMutation.isPending}
      width={600}
    >
      <p>选择要从当前聚簇中移出的热点（将创建新聚簇或设为未分组）：</p>

      <Space direction="vertical" style={{ width: "100%", marginTop: 16 }}>
        <Checkbox
          checked={isAllSelected}
          indeterminate={isIndeterminate}
          onChange={(e) => handleSelectAll(e.target.checked)}
        >
          全选 ({selectedHotspots.length}/{hotspots.length})
        </Checkbox>

        <div
          style={{
            maxHeight: 400,
            overflowY: "auto",
            border: "1px solid #f0f0f0",
            borderRadius: 4,
            padding: 12,
          }}
        >
          {hotspots.map((hotspot) => (
            <div key={hotspot.id} style={{ marginBottom: 8 }}>
              <Checkbox
                checked={selectedHotspots.includes(hotspot.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedHotspots([...selectedHotspots, hotspot.id]);
                  } else {
                    setSelectedHotspots(selectedHotspots.filter((id) => id !== hotspot.id));
                  }
                }}
              >
                {hotspot.keyword}
                <span style={{ color: "#999", marginLeft: 8, fontSize: 12 }}>
                  (出现 {hotspot.appearance_count} 次)
                </span>
              </Checkbox>
            </div>
          ))}
        </div>
      </Space>

      <p style={{ marginTop: 16, color: "#666", fontSize: 12 }}>
        提示：
        <br />
        - 如果选择多个热点，将为它们创建新的聚簇
        <br />
        - 如果只选择1个热点，该热点将变为未分组状态
        <br />- 不能移出所有热点（这会删除整个聚簇）
      </p>
    </Modal>
  );
}
