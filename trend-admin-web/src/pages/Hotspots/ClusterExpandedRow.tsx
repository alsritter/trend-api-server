import { Table, Space, Button, Tag, Tooltip, Modal, message } from "antd";
import { EyeOutlined, DeleteOutlined } from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import type { HotspotDetail } from "@/types/api";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";

interface ClusterExpandedRowProps {
  clusterId: number;
  onViewDetail: (hotspot: HotspotDetail) => void;
}

export function ClusterExpandedRow({
  clusterId,
  onViewDetail
}: ClusterExpandedRowProps) {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ["clusterHotspots", clusterId],
    queryFn: () => hotspotsApi.getClusterHotspots(clusterId)
  });

  // 删除热点的 mutation
  const deleteHotspotMutation = useMutation({
    mutationFn: (hotspotId: number) => hotspotsApi.delete(hotspotId),
    onSuccess: () => {
      message.success("热点删除成功");
      queryClient.invalidateQueries({ queryKey: ["clusterHotspots"] });
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  const hotspotColumns: ColumnsType<HotspotDetail> = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80
    },
    {
      title: "关键词",
      dataIndex: "keyword",
      key: "keyword",
      width: 250
    },
    {
      title: "标准化关键词",
      dataIndex: "normalized_keyword",
      key: "normalized_keyword",
      width: 250
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => {
        const statusInfo = STATUS_MAP[status];
        return (
          <Tag color={statusInfo?.color || "default"}>
            {statusInfo?.label || status}
          </Tag>
        );
      }
    },
    {
      title: "平台",
      dataIndex: "platforms",
      key: "platforms",
      width: 200,
      render: (platforms: HotspotDetail["platforms"]) => (
        <Space size={4} wrap>
          {platforms.map((p, idx) => (
            <Tag key={idx} color="blue">
              {PLATFORM_MAP[p.platform] || p.platform}
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: "出现次数",
      dataIndex: "appearance_count",
      key: "appearance_count",
      width: 100
    },
    {
      title: "首次出现",
      dataIndex: "first_seen_at",
      key: "first_seen_at",
      width: 180,
      render: (date: string) => dayjs(date).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      title: "操作",
      key: "action",
      width: 120,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: "确认删除",
                  content: `确定要删除热点"${record.keyword}"吗？`,
                  onOk: () => deleteHotspotMutation.mutate(record.id)
                });
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div style={{ 
      backgroundColor: "#fafafa", 
      padding: "16px", 
      borderRadius: "4px" 
    }}>
      <Table
        columns={hotspotColumns}
        dataSource={data?.items || []}
        rowKey="id"
        size="small"
        pagination={false}
        loading={isLoading}
        bordered
      />
    </div>
  );
}
