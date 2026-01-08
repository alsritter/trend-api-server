import { Space, Button, Tag, Tooltip, Modal, message, Row, Col, Card, Typography, Descriptions } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import type { HotspotDetail } from "@/types/api";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";

const { Text } = Typography;

interface ClusterExpandedRowProps {
  clusterId: number;
}

export function ClusterExpandedRow({
  clusterId
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

  // 渲染单个热点的详细信息（两列布局）
  const renderHotspotDetail = (hotspot: HotspotDetail) => (
    <Card 
      key={hotspot.id}
      size="small" 
      style={{ marginBottom: 16 }}
      extra={
        <Space size="small">
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: "确认删除",
                  content: `确定要删除热点"${hotspot.keyword}"吗？`,
                  onOk: () => deleteHotspotMutation.mutate(hotspot.id)
                });
              }}
            />
          </Tooltip>
        </Space>
      }
    >
      <Row gutter={[24, 16]}>
        {/* 左列 */}
        <Col span={12}>
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="ID">{hotspot.id}</Descriptions.Item>
            <Descriptions.Item label="关键词">
              <Text strong>{hotspot.keyword}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="标准化关键词">
              {hotspot.normalized_keyword}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_MAP[hotspot.status]?.color}>
                {STATUS_MAP[hotspot.status]?.label || hotspot.status}
              </Tag>
            </Descriptions.Item>
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
            <Descriptions.Item label="出现次数">
              {hotspot.appearance_count}
            </Descriptions.Item>
            <Descriptions.Item label="首次出现">
              {dayjs(hotspot.first_seen_at).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
            <Descriptions.Item label="最后出现">
              {dayjs(hotspot.last_seen_at).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
          </Descriptions>
        </Col>
        
        {/* 右列 */}
        <Col span={12}>
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="平台信息">
              <Space direction="vertical" style={{ width: '100%' }}>
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
            <Descriptions.Item label="向量模型">
              {hotspot.embedding_model}
            </Descriptions.Item>
          </Descriptions>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div style={{ 
      backgroundColor: "#fafafa", 
      padding: "16px", 
      borderRadius: "4px" 
    }}>
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>加载中...</div>
      ) : (
        <Space direction="vertical" style={{ width: '100%' }}>
          {(data?.items || []).map(renderHotspotDetail)}
        </Space>
      )}
    </div>
  );
}
