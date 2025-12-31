import { Modal, Descriptions, Tag, Typography, Card, Space } from "antd";
import { FireOutlined } from "@ant-design/icons";
import { STATUS_MAP } from "./HotspotTableColumns";
import type { HotspotDetail } from "@/types/api";

const { Text, Paragraph } = Typography;

export interface HotspotDetailModalProps {
  visible: boolean;
  hotspot: HotspotDetail | null;
  onClose: () => void;
}

export const HotspotDetailModal = ({
  visible,
  hotspot,
  onClose
}: HotspotDetailModalProps) => {
  if (!hotspot) return null;

  return (
    <Modal
      title={
        <Space>
          <FireOutlined style={{ color: "#1890ff" }} />
          <span>热点详情</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      <Descriptions bordered column={2} size="small">
        <Descriptions.Item label="ID">{hotspot.id}</Descriptions.Item>
        <Descriptions.Item label="热词">{hotspot.keyword}</Descriptions.Item>
        <Descriptions.Item label="归一化关键词">
          {hotspot.normalized_keyword}
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={STATUS_MAP[hotspot.status]?.color || "default"}>
            {STATUS_MAP[hotspot.status]?.label || hotspot.status}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="出现次数">
          {hotspot.appearance_count}
        </Descriptions.Item>
        <Descriptions.Item label="簇ID">
          {hotspot.cluster_id || "未分组"}
        </Descriptions.Item>
        <Descriptions.Item label="向量模型" span={2}>
          {hotspot.embedding_model || "N/A"}
        </Descriptions.Item>
        <Descriptions.Item label="首次发现时间" span={2}>
          {new Date(hotspot.first_seen_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
        <Descriptions.Item label="最后出现时间" span={2}>
          {new Date(hotspot.last_seen_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
        <Descriptions.Item label="爬取次数">
          {hotspot.crawl_count}
        </Descriptions.Item>
        <Descriptions.Item label="爬取失败次数">
          <Text
            type={hotspot.crawl_failed_count > 0 ? "danger" : "secondary"}
          >
            {hotspot.crawl_failed_count}
          </Text>
        </Descriptions.Item>
        {hotspot.last_crawled_at && (
          <Descriptions.Item label="最后爬取时间" span={2}>
            {new Date(hotspot.last_crawled_at).toLocaleString("zh-CN")}
          </Descriptions.Item>
        )}
        <Descriptions.Item label="是否过滤">
          {hotspot.is_filtered ? (
            <Tag color="red">已过滤</Tag>
          ) : (
            <Tag color="green">正常</Tag>
          )}
        </Descriptions.Item>
        {hotspot.filter_reason && (
          <Descriptions.Item label="过滤原因" span={2}>
            <Paragraph style={{ margin: 0 }}>
              {hotspot.filter_reason}
            </Paragraph>
          </Descriptions.Item>
        )}
        <Descriptions.Item label="平台信息" span={2}>
          <Space direction="vertical" style={{ width: "100%" }}>
            {hotspot.platforms.map((p, idx) => (
              <Card key={idx} size="small" style={{ marginBottom: 8 }}>
                <Space direction="vertical" size={0}>
                  <Text>
                    <strong>平台:</strong> {p.platform}
                  </Text>
                  <Text>
                    <strong>排名:</strong> {p.rank}
                  </Text>
                  <Text>
                    <strong>热度:</strong> {p.heat_score || "N/A"}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    发现时间: {new Date(p.seen_at).toLocaleString("zh-CN")}
                  </Text>
                </Space>
              </Card>
            ))}
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="创建时间" span={2}>
          {new Date(hotspot.created_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
        <Descriptions.Item label="更新时间" span={2}>
          {new Date(hotspot.updated_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  );
};
