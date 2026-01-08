import { Drawer, Descriptions, Tag, Space } from "antd";
import type { HotspotDetail } from "@/types/api";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";

interface HotspotDetailDrawerProps {
  visible: boolean;
  hotspot: HotspotDetail | null;
  onClose: () => void;
}

export function HotspotDetailDrawer({
  visible,
  hotspot,
  onClose
}: HotspotDetailDrawerProps) {
  return (
    <Drawer
      title="热点详情"
      placement="right"
      width={720}
      open={visible}
      onClose={onClose}
    >
      {hotspot && (
        <Descriptions column={1} bordered>
          <Descriptions.Item label="ID">{hotspot.id}</Descriptions.Item>
          <Descriptions.Item label="关键词">
            {hotspot.keyword}
          </Descriptions.Item>
          <Descriptions.Item label="标准化关键词">
            {hotspot.normalized_keyword}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={STATUS_MAP[hotspot.status]?.color}>
              {STATUS_MAP[hotspot.status]?.label || hotspot.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="聚簇ID">
            {hotspot.cluster_id}
          </Descriptions.Item>
          <Descriptions.Item label="出现次数">
            {hotspot.appearance_count}
          </Descriptions.Item>
          <Descriptions.Item label="首次出现">
            {dayjs(hotspot.first_seen_at).format("YYYY-MM-DD HH:mm:ss")}
          </Descriptions.Item>
          <Descriptions.Item label="最后出现">
            {dayjs(hotspot.last_seen_at).format("YYYY-MM-DD HH:mm:ss")}
          </Descriptions.Item>
          <Descriptions.Item label="向量模型">
            {hotspot.embedding_model}
          </Descriptions.Item>
          <Descriptions.Item label="是否过滤">
            {hotspot.is_filtered ? (
              <Tag color="red">是</Tag>
            ) : (
              <Tag color="green">否</Tag>
            )}
          </Descriptions.Item>
          {hotspot.filter_reason && (
            <Descriptions.Item label="过滤原因">
              {hotspot.filter_reason}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="爬取次数">
            {hotspot.crawl_count}
          </Descriptions.Item>
          {hotspot.last_crawled_at && (
            <Descriptions.Item label="最后爬取时间">
              {dayjs(hotspot.last_crawled_at).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="平台信息">
            <Space direction="vertical">
              {hotspot.platforms.map((platform, index) => (
                <div key={index}>
                  <Tag color="blue">
                    {PLATFORM_MAP[platform.platform] || platform.platform}
                  </Tag>
                  <span>排名: {platform.rank}</span>
                  {platform.heat_score && (
                    <span> | 热度: {platform.heat_score}</span>
                  )}
                  <br />
                  <span style={{ color: "#999", fontSize: 12 }}>
                    {dayjs(platform.seen_at).format("YYYY-MM-DD HH:mm:ss")}
                  </span>
                </div>
              ))}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(hotspot.created_at).format("YYYY-MM-DD HH:mm:ss")}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(hotspot.updated_at).format("YYYY-MM-DD HH:mm:ss")}
          </Descriptions.Item>
        </Descriptions>
      )}
    </Drawer>
  );
}
