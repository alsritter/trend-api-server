import { Modal, Table, Tag, Space, Spin, Alert } from "antd";
import { ClusterOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { clustersApi } from "@/api/clusters";
import { STATUS_MAP } from "./HotspotTableColumns";
import type { HotspotDetail, GetClusterHotspotsResponse } from "@/types/api";
import type { ColumnsType } from "antd/es/table";

export interface ClusterHotspotsModalProps {
  visible: boolean;
  clusterId: number | null;
  onClose: () => void;
}

export const ClusterHotspotsModal = ({
  visible,
  clusterId,
  onClose
}: ClusterHotspotsModalProps) => {
  const { data, isLoading, error } = useQuery<GetClusterHotspotsResponse>({
    queryKey: ["cluster-hotspots", clusterId],
    queryFn: () => clustersApi.getHotspots(clusterId!),
    enabled: visible && clusterId !== null
  });

  const columns: ColumnsType<HotspotDetail> = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80
    },
    {
      title: "热词",
      dataIndex: "keyword",
      key: "keyword",
      width: 200
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: HotspotDetail["status"]) => (
        <Tag color={STATUS_MAP[status]?.color || "default"}>
          {STATUS_MAP[status]?.label || status}
        </Tag>
      )
    },
    {
      title: "出现次数",
      dataIndex: "appearance_count",
      key: "appearance_count",
      width: 100,
      align: "center"
    },
    {
      title: "首次发现",
      dataIndex: "first_seen_at",
      key: "first_seen_at",
      width: 160,
      render: (time: string) => new Date(time).toLocaleString("zh-CN")
    },
    {
      title: "最后出现",
      dataIndex: "last_seen_at",
      key: "last_seen_at",
      width: 160,
      render: (time: string) => new Date(time).toLocaleString("zh-CN")
    }
  ];

  return (
    <Modal
      title={
        <Space>
          <ClusterOutlined style={{ color: "#1890ff" }} />
          <span>同簇热点 (簇ID: {clusterId})</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={900}
    >
      {isLoading && (
        <div style={{ textAlign: "center", padding: "40px 0" }}>
          <Spin size="large" />
        </div>
      )}

      {error && (
        <Alert
          message="加载失败"
          description="获取同簇热点数据失败,请稍后重试"
          type="error"
          showIcon
        />
      )}

      {data && (
        <>
          <Alert
            message={`共找到 ${data.count} 个相关热点`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Table
            columns={columns}
            dataSource={data.items}
            rowKey="id"
            pagination={false}
            size="small"
            scroll={{ y: 400 }}
          />
        </>
      )}
    </Modal>
  );
};
