import { Drawer, Descriptions, Tag, Space, Card, Typography, Button, Dropdown, message } from "antd";
import type { HotspotDetail, HotspotStatus } from "@/types/api";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";
import { hotspotsApi } from "@/api/hotspots";
import { useState } from "react";
import { DownOutlined } from "@ant-design/icons";

const { Text } = Typography;

interface HotspotDetailDrawerProps {
  visible: boolean;
  hotspot: HotspotDetail | null;
  onClose: () => void;
  onUpdate?: () => void; // 更新成功后的回调
}

export function HotspotDetailDrawer({
  visible,
  hotspot,
  onClose,
  onUpdate
}: HotspotDetailDrawerProps) {
  const [loading, setLoading] = useState(false);

  // 快速状态切换选项
  const statusOptions = [
    { key: "validated", label: "已验证", color: "green" },
    { key: "crawling", label: "爬取中", color: "blue" },
    { key: "crawled", label: "已爬取", color: "cyan" },
    { key: "analyzing", label: "分析中", color: "purple" },
    { key: "analyzed", label: "已分析", color: "geekblue" },
    { key: "archived", label: "已归档", color: "default" },
  ];

  // 处理状态更新
  const handleStatusChange = async (newStatus: HotspotStatus, setAsRepresentative: boolean = true) => {
    if (!hotspot) return;

    try {
      setLoading(true);
      const response = await hotspotsApi.updateStatusAndSetRepresentative(hotspot.id, {
        status: newStatus,
        set_as_representative: setAsRepresentative,
      });

      if (response.success) {
        message.success(response.message, 1500);
        onUpdate?.(); // 触发父组件刷新
      } else {
        message.error("状态更新失败");
      }
    } catch (error: any) {
      message.error(error.message || "状态更新失败");
    } finally {
      setLoading(false);
    }
  };

  // 构建下拉菜单项
  const menuItems = statusOptions.map((option) => ({
    key: option.key,
    label: (
      <span>
        <Tag color={option.color}>{option.label}</Tag>
        {hotspot?.cluster_id && <span style={{ fontSize: 12, color: "#999" }}>(设为代表)</span>}
      </span>
    ),
    onClick: () => handleStatusChange(option.key as HotspotStatus),
  }));

  return (
    <Drawer
      title={
        <Space>
          <span>热点详情</span>
          {hotspot && (
            <Dropdown
              menu={{ items: menuItems }}
              placement="bottomLeft"
              disabled={loading}
            >
              <Button type="primary" size="small" loading={loading}>
                快速切换状态 <DownOutlined />
              </Button>
            </Dropdown>
          )}
        </Space>
      }
      placement="right"
      width={800}
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
          
          {/* AI 分析信息 */}
          {hotspot.primary_category && (
            <Descriptions.Item label="主要分类">
              <Tag color="blue">{hotspot.primary_category}</Tag>
            </Descriptions.Item>
          )}
          
          {hotspot.confidence !== undefined && hotspot.confidence !== null && (
            <Descriptions.Item label="置信度">
              <Text type={hotspot.confidence >= 0.8 ? "success" : hotspot.confidence >= 0.5 ? "warning" : "danger"}>
                {(hotspot.confidence * 100).toFixed(1)}%
              </Text>
            </Descriptions.Item>
          )}
          
          {hotspot.tags && hotspot.tags.length > 0 && (
            <Descriptions.Item label="标签">
              <Space wrap>
                {hotspot.tags.map((tag, idx) => (
                  <Tag key={idx} color="cyan">{tag}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          
          {hotspot.platform_url && (
            <Descriptions.Item label="平台链接">
              <a href={hotspot.platform_url} target="_blank" rel="noopener noreferrer">
                查看原文
              </a>
            </Descriptions.Item>
          )}
          
          {hotspot.opportunities && hotspot.opportunities.length > 0 && (
            <Descriptions.Item label="初筛机会">
              <Space direction="vertical" style={{ width: "100%" }}>
                {hotspot.opportunities.map((opp, idx) => (
                  <Card key={idx} size="small" style={{ backgroundColor: "#f0f9ff" }}>
                    💡 {opp}
                  </Card>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          
          {hotspot.reasoning_keep && hotspot.reasoning_keep.length > 0 && (
            <Descriptions.Item label="保留原因">
              <Space direction="vertical" style={{ width: "100%" }}>
                {hotspot.reasoning_keep.map((reason, idx) => (
                  <Card key={idx} size="small" style={{ backgroundColor: "#f6ffed" }}>
                    ✓ {reason}
                  </Card>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          
          {hotspot.reasoning_risk && hotspot.reasoning_risk.length > 0 && (
            <Descriptions.Item label="风险提示">
              <Space direction="vertical" style={{ width: "100%" }}>
                {hotspot.reasoning_risk.map((risk, idx) => (
                  <Card key={idx} size="small" style={{ backgroundColor: "#fff1f0" }}>
                    ⚠ {risk}
                  </Card>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          
          {/* 基础信息 */}
          <Descriptions.Item label="聚簇ID">
            {hotspot.cluster_id || "未分组"}
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
          
          {/* 第一阶段拒绝信息 */}
          {hotspot.rejection_reason && (
            <Descriptions.Item label="第一阶段拒绝原因">
              <Card size="small" style={{ backgroundColor: "#fff1f0" }}>
                🚫 {hotspot.rejection_reason}
              </Card>
            </Descriptions.Item>
          )}
          {hotspot.rejected_at && (
            <Descriptions.Item label="第一阶段拒绝时间">
              {dayjs(hotspot.rejected_at).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
          )}
          
          {/* 第二阶段拒绝信息 */}
          {hotspot.second_stage_rejection_reason && (
            <Descriptions.Item label="第二阶段拒绝原因">
              <Card size="small" style={{ backgroundColor: "#fff7e6" }}>
                ⛔ {hotspot.second_stage_rejection_reason}
              </Card>
            </Descriptions.Item>
          )}
          {hotspot.second_stage_rejected_at && (
            <Descriptions.Item label="第二阶段拒绝时间">
              {dayjs(hotspot.second_stage_rejected_at).format("YYYY-MM-DD HH:mm:ss")}
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
