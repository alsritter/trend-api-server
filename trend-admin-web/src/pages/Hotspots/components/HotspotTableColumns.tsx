import {
  Space,
  Tag,
  Typography,
  Tooltip,
  Badge,
  Button,
  Popconfirm
} from "antd";

const { Text } = Typography;
import {
  FireOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  DeleteOutlined
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { HotspotDetail, HotspotStatus, PlatformInfo } from "@/types/api";

// 状态标签映射
export const STATUS_MAP: Record<HotspotStatus, { label: string; color: string }> = {
  pending_validation: { label: "待验证", color: "default" },
  validated: { label: "已验证", color: "blue" },
  rejected: { label: "已过滤", color: "red" },
  crawling: { label: "爬取中", color: "processing" },
  crawled: { label: "已爬取", color: "cyan" },
  analyzing: { label: "分析中", color: "purple" },
  analyzed: { label: "已分析", color: "green" },
  archived: { label: "已归档", color: "default" }
};

export interface HotspotTableColumnsProps {
  onViewDetail: (record: HotspotDetail) => void;
  onDelete: (hotspotId: number) => void;
  onViewCluster?: (clusterId: number) => void;
  isDeleting: boolean;
}

export const getHotspotTableColumns = ({
  onViewDetail,
  onDelete,
  onViewCluster,
  isDeleting
}: HotspotTableColumnsProps): ColumnsType<HotspotDetail> => [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
    width: 80,
    fixed: "left"
  },
  {
    title: "热词",
    dataIndex: "keyword",
    key: "keyword",
    width: 220,
    fixed: "left",
    render: (text: string, record: HotspotDetail) => (
      <Space direction="vertical" size={0}>
        <Text strong style={{ color: "#1890ff" }}>
          <FireOutlined style={{ marginRight: 4 }} />
          {text}
        </Text>
        {record.cluster_id && (
          <Space size={4}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              簇ID: {record.cluster_id}
            </Text>
            {onViewCluster && (
              <Button
                type="link"
                size="small"
                style={{ fontSize: 11, padding: 0, height: "auto" }}
                onClick={() => onViewCluster(record.cluster_id!)}
              >
                查看同簇
              </Button>
            )}
          </Space>
        )}
      </Space>
    )
  },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    width: 100,
    render: (status: HotspotStatus) => (
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
    align: "center",
    render: (count: number) => (
      <Badge
        count={count}
        showZero
        color="#52c41a"
        style={{ fontSize: 14 }}
      />
    )
  },
  {
    title: "平台",
    dataIndex: "platforms",
    key: "platforms",
    width: 150,
    render: (platforms: PlatformInfo[]) => (
      <Space size={[0, 4]} wrap>
        {platforms.slice(0, 3).map((p, idx) => (
          <Tooltip
            key={idx}
            title={`排名: ${p.rank}, 热度: ${p.heat_score || "N/A"}`}
          >
            <Tag color="blue" style={{ fontSize: 11 }}>
              {p.platform}
            </Tag>
          </Tooltip>
        ))}
        {platforms.length > 3 && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            +{platforms.length - 3}
          </Text>
        )}
      </Space>
    )
  },
  {
    title: "首次发现",
    dataIndex: "first_seen_at",
    key: "first_seen_at",
    width: 160,
    render: (time: string) => (
      <Text type="secondary" style={{ fontSize: 12 }}>
        {new Date(time).toLocaleString("zh-CN")}
      </Text>
    )
  },
  {
    title: "最后出现",
    dataIndex: "last_seen_at",
    key: "last_seen_at",
    width: 160,
    render: (time: string) => (
      <Text type="secondary" style={{ fontSize: 12 }}>
        {new Date(time).toLocaleString("zh-CN")}
      </Text>
    )
  },
  {
    title: "爬取信息",
    key: "crawl_info",
    width: 120,
    align: "center",
    render: (_, record: HotspotDetail) => (
      <Space direction="vertical" size={0}>
        <Text style={{ fontSize: 12 }}>次数: {record.crawl_count}</Text>
        {record.crawl_failed_count > 0 && (
          <Text type="danger" style={{ fontSize: 12 }}>
            失败: {record.crawl_failed_count}
          </Text>
        )}
      </Space>
    )
  },
  {
    title: "过滤状态",
    dataIndex: "is_filtered",
    key: "is_filtered",
    width: 100,
    align: "center",
    render: (isFiltered: boolean) =>
      isFiltered ? (
        <CloseCircleOutlined style={{ color: "#ff4d4f", fontSize: 18 }} />
      ) : (
        <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 18 }} />
      )
  },
  {
    title: "操作",
    key: "actions",
    width: 180,
    fixed: "right",
    render: (_, record: HotspotDetail) => (
      <Space size="small">
        <Tooltip title="查看详情">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => onViewDetail(record)}
          >
            详情
          </Button>
        </Tooltip>
        <Popconfirm
          title="确认删除"
          description={`确定要删除热点 "${record.keyword}" 吗？`}
          onConfirm={() => onDelete(record.id)}
          okText="确定"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            loading={isDeleting}
          >
            删除
          </Button>
        </Popconfirm>
      </Space>
    )
  }
];
