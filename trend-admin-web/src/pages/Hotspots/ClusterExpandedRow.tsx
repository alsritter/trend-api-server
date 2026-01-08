import {
  Space,
  Button,
  Tag,
  Tooltip,
  Modal,
  message,
  Row,
  Col,
  Card,
  Typography,
  Descriptions,
  Collapse,
  Table
} from "antd";
import {
  DeleteOutlined,
  LinkOutlined,
  FileTextOutlined
} from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import { contentsApi } from "@/api/contents";
import type { HotspotDetail } from "@/types/api";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";
import { useState, useEffect } from "react";
import { formatDateTime } from "@/utils/format";

const { Text } = Typography;

interface ClusterExpandedRowProps {
  clusterId: number;
}

export function ClusterExpandedRow({ clusterId }: ClusterExpandedRowProps) {
  const queryClient = useQueryClient();
  const [expandedHotspotIds, setExpandedHotspotIds] = useState<number[]>([]);
  const [contentTotals, setContentTotals] = useState<Record<number, number>>(
    {}
  );

  const { data, isLoading } = useQuery({
    queryKey: ["clusterHotspots", clusterId],
    queryFn: () => hotspotsApi.getClusterHotspots(clusterId)
  });

  // 当热点列表加载完成后，批量获取内容数量
  useEffect(() => {
    if (data?.items && data.items.length > 0) {
      // 获取所有热点ID和主要平台
      const hotspotIds = data.items.map((item: HotspotDetail) => item.id);
      const primaryPlatform = data.items[0].platforms[0]?.platform || 'xhs';
      
      // 批量查询内容数量
      contentsApi.getContentCounts(hotspotIds, primaryPlatform)
        .then((counts) => {
          // 将字符串键转换为数字键
          const numericCounts: Record<number, number> = {};
          Object.entries(counts).forEach(([key, value]) => {
            numericCounts[parseInt(key)] = value;
          });
          setContentTotals(numericCounts);
        })
        .catch((error) => {
          console.error('Failed to fetch content counts:', error);
        });
    }
  }, [data?.items]);

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

  // 切换热点内容展开状态
  const toggleHotspotContent = (hotspotId: number) => {
    setExpandedHotspotIds((prev) =>
      prev.includes(hotspotId)
        ? prev.filter((id) => id !== hotspotId)
        : [...prev, hotspotId]
    );
  };

  // 渲染热点内容表格
  const HotspotContentTable = ({
    hotspotId,
    platforms
  }: {
    hotspotId: number;
    platforms: any[];
  }) => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);

    // 获取热点的主要平台
    const primaryPlatform =
      platforms.length > 0 ? platforms[0].platform : "xhs";

    const { data: contentsData, isLoading: contentsLoading } = useQuery({
      queryKey: ["hotspotContents", hotspotId, primaryPlatform, page, pageSize],
      queryFn: () =>
        contentsApi.getNotes(primaryPlatform, {
          hotspot_id: hotspotId,
          page,
          page_size: pageSize
        }),
      enabled: expandedHotspotIds.includes(hotspotId)
    });

    // 当数据加载成功时，更新内容总数
    useEffect(() => {
      if (contentsData?.total !== undefined) {
        setContentTotals((prev) => ({
          ...prev,
          [hotspotId]: contentsData.total
        }));
      }
    }, [contentsData?.total, hotspotId]);

    // 根据平台动态生成列配置
    const getColumns = () => {
      const commonColumns = [
        {
          title: "标题",
          dataIndex: "title",
          key: "title",
          ellipsis: true,
          width: 250
        },
        {
          title: "作者",
          dataIndex: "nickname",
          key: "nickname",
          width: 120
        }
      ];

      if (primaryPlatform === "xhs") {
        return [
          ...commonColumns,
          {
            title: "点赞",
            dataIndex: "liked_count",
            key: "liked_count",
            width: 80
          },
          {
            title: "收藏",
            dataIndex: "collected_count",
            key: "collected_count",
            width: 80
          },
          {
            title: "评论",
            dataIndex: "comment_count",
            key: "comment_count",
            width: 80
          },
          {
            title: "发布时间",
            dataIndex: "time",
            key: "time",
            width: 160,
            render: formatDateTime
          }
        ];
      } else if (primaryPlatform === "dy" || primaryPlatform === "ks") {
        return [
          ...commonColumns,
          {
            title: "播放量",
            dataIndex: "video_play_count",
            key: "video_play_count",
            width: 100
          },
          {
            title: "点赞",
            dataIndex: "liked_count",
            key: "liked_count",
            width: 80
          },
          {
            title: "评论",
            dataIndex: "comment_count",
            key: "comment_count",
            width: 80
          },
          {
            title: "发布时间",
            dataIndex: "time",
            key: "time",
            width: 160,
            render: formatDateTime
          }
        ];
      } else if (primaryPlatform === "bili") {
        return [
          ...commonColumns,
          {
            title: "播放量",
            dataIndex: "video_play_count",
            key: "video_play_count",
            width: 100
          },
          {
            title: "弹幕",
            dataIndex: "video_danmaku",
            key: "video_danmaku",
            width: 80
          },
          {
            title: "评论",
            dataIndex: "video_comment",
            key: "video_comment",
            width: 80
          },
          {
            title: "发布时间",
            dataIndex: "time",
            key: "time",
            width: 160,
            render: formatDateTime
          }
        ];
      }

      return [
        ...commonColumns,
        {
          title: "发布时间",
          dataIndex: "time",
          key: "time",
          width: 160,
          render: formatDateTime
        }
      ];
    };

    return (
      <Table
        columns={getColumns()}
        dataSource={contentsData?.items || []}
        rowKey="id"
        loading={contentsLoading}
        size="small"
        pagination={{
          current: page,
          pageSize: pageSize,
          total: contentsData?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage);
            setPageSize(newPageSize);
          }
        }}
      />
    );
  };

  // 渲染单个热点的详细信息（两列布局）
  const renderHotspotDetail = (hotspot: HotspotDetail) => {
    const isExpanded = expandedHotspotIds.includes(hotspot.id);

    return (
      <Card
        key={hotspot.id}
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          <Space size="small">
            <Tooltip title={isExpanded ? "收起内容" : "查看爬取内容"}>
              <Button
                type="text"
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => toggleHotspotContent(hotspot.id)}
              >
                {isExpanded ? "收起" : "查看内容"} (
                {contentTotals[hotspot.id] ?? hotspot.crawl_count ?? 0})
              </Button>
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
              {hotspot.platform_url && (
                <Descriptions.Item label="平台链接">
                  <a
                    href={hotspot.platform_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontWeight: 500 }}
                  >
                    <LinkOutlined /> 查看原文
                  </a>
                </Descriptions.Item>
              )}
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
              {hotspot.confidence !== undefined &&
                hotspot.confidence !== null && (
                  <Descriptions.Item label="置信度">
                    <Text
                      type={
                        hotspot.confidence >= 0.8
                          ? "success"
                          : hotspot.confidence >= 0.5
                          ? "warning"
                          : "danger"
                      }
                    >
                      {(hotspot.confidence * 100).toFixed(1)}%
                    </Text>
                  </Descriptions.Item>
                )}
              {hotspot.tags && hotspot.tags.length > 0 && (
                <Descriptions.Item label="标签">
                  <Space wrap>
                    {hotspot.tags.map((tag, idx) => (
                      <Tag key={idx} color="cyan">
                        {tag}
                      </Tag>
                    ))}
                  </Space>
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
                <Space direction="vertical" style={{ width: "100%" }}>
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
                      <Card
                        key={idx}
                        size="small"
                        style={{ backgroundColor: "#f0f9ff" }}
                      >
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
                      <Card
                        key={idx}
                        size="small"
                        style={{ backgroundColor: "#f6ffed" }}
                      >
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
                      <Card
                        key={idx}
                        size="small"
                        style={{ backgroundColor: "#fff1f0" }}
                      >
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

        {/* 爬取内容展开区域 */}
        {isExpanded && (
          <div style={{ marginTop: 16 }}>
            <Collapse
              activeKey={["content"]}
              bordered={false}
              items={[
                {
                  key: "content",
                  label: <Text strong>爬取内容列表</Text>,
                  children: (
                    <HotspotContentTable
                      hotspotId={hotspot.id}
                      platforms={hotspot.platforms}
                    />
                  )
                }
              ]}
            />
          </div>
        )}
      </Card>
    );
  };

  return (
    <div
      style={{
        backgroundColor: "#fafafa",
        padding: "16px",
        borderRadius: "4px"
      }}
    >
      {isLoading ? (
        <div style={{ textAlign: "center", padding: "20px" }}>加载中...</div>
      ) : (
        <Space direction="vertical" style={{ width: "100%" }}>
          {(data?.items || []).map(renderHotspotDetail)}
        </Space>
      )}
    </div>
  );
}
