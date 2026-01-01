import { Card, Tree, Table, Space, Button, message, Drawer, Descriptions, Tag, Modal, Input, Select, Checkbox, DatePicker, Dropdown } from "antd";
import { ReloadOutlined, DeleteOutlined, EditOutlined, MergeCellsOutlined, SwapOutlined, PlusOutlined, FilterOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { clustersApi } from "@/api/clusters";
import { hotspotsApi } from "@/api/hotspots";
import type { ClusterInfo, HotspotDetail } from "@/types/api";
import type { DataNode } from "antd/es/tree";
import { STATUS_MAP } from "./components/HotspotTableColumns";
import type { Dayjs } from 'dayjs';

function Hotspots() {
  const queryClient = useQueryClient();
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(null);
  const [hotspotDetailVisible, setHotspotDetailVisible] = useState(false);
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [newClusterName, setNewClusterName] = useState("");
  const [mergeModalVisible, setMergeModalVisible] = useState(false);
  const [selectedClusters, setSelectedClusters] = useState<number[]>([]);
  const [moveHotspotModalVisible, setMoveHotspotModalVisible] = useState(false);
  const [selectedHotspotIds, setSelectedHotspotIds] = useState<number[]>([]);
  const [targetClusterId, setTargetClusterId] = useState<number | null>(null);
  const [createClusterModalVisible, setCreateClusterModalVisible] = useState(false);
  const [createClusterName, setCreateClusterName] = useState("");
  const [clusterSearchKeyword, setClusterSearchKeyword] = useState("");
  const [filterStatusList, setFilterStatusList] = useState<string[]>([]);
  const [filterDateRange, setFilterDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);

  // 获取所有聚簇
  const { data: clustersData, refetch: refetchClusters, isLoading: clustersLoading } = useQuery({
    queryKey: ["clusters", clusterSearchKeyword],
    queryFn: async () => {
      const allClusters = await clustersApi.list();

      // 如果有搜索词,使用相似度搜索过滤聚簇
      if (clusterSearchKeyword.trim()) {
        const searchResult = await hotspotsApi.list({
          page: 1,
          page_size: 1000,
          similarity_search: clusterSearchKeyword.trim(),
          similarity_threshold: 0.5
        });

        // 获取搜索到的热点所属的聚簇ID
        const matchedClusterIds = new Set(
          searchResult.items
            .filter(h => h.cluster_id !== null)
            .map(h => h.cluster_id!)
        );

        // 过滤出包含匹配热点的聚簇
        return {
          ...allClusters,
          items: allClusters.items.filter(c => matchedClusterIds.has(c.id))
        };
      }

      return allClusters;
    }
  });

  // 应用过滤条件
  const filteredClusters = clustersData?.items.filter((cluster: ClusterInfo) => {
    // 状态过滤
    if (filterStatusList.length > 0) {
      const hasMatchingStatus = cluster.statuses.some(status => filterStatusList.includes(status));
      if (!hasMatchingStatus) return false;
    }

    // 时间过滤
    if (filterDateRange && filterDateRange[0] && filterDateRange[1]) {
      const clusterTime = new Date(cluster.last_hotspot_update).getTime();
      const startTime = filterDateRange[0].valueOf();
      const endTime = filterDateRange[1].valueOf();
      if (clusterTime < startTime || clusterTime > endTime) return false;
    }

    return true;
  }) || [];

  // 获取选中聚簇的热点
  const { data: hotspotsData, isLoading: hotspotsLoading } = useQuery({
    queryKey: ["cluster-hotspots", selectedClusterId],
    queryFn: () => selectedClusterId ? clustersApi.getHotspots(selectedClusterId) : Promise.resolve(null),
    enabled: !!selectedClusterId
  });

  // 删除聚簇
  const deleteClusterMutation = useMutation({
    mutationFn: clustersApi.delete,
    onSuccess: () => {
      message.success("聚簇删除成功");
      setSelectedClusterId(null);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 删除热点
  const deleteHotspotMutation = useMutation({
    mutationFn: hotspotsApi.delete,
    onSuccess: () => {
      message.success("热点删除成功");
      queryClient.invalidateQueries({ queryKey: ["cluster-hotspots", selectedClusterId] });
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 重命名聚簇
  const renameClusterMutation = useMutation({
    mutationFn: ({ clusterId, clusterName }: { clusterId: number; clusterName: string }) =>
      clustersApi.update(clusterId, { cluster_name: clusterName }),
    onSuccess: () => {
      message.success("聚簇重命名成功");
      setRenameModalVisible(false);
      setNewClusterName("");
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`重命名失败: ${error.message}`);
    }
  });

  // 合并聚簇
  const mergeClustersMutation = useMutation({
    mutationFn: clustersApi.merge,
    onSuccess: () => {
      message.success("聚簇合并成功");
      setMergeModalVisible(false);
      setSelectedClusters([]);
      setSelectedClusterId(null);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`合并失败: ${error.message}`);
    }
  });

  // 移动热点到聚簇
  const moveHotspotMutation = useMutation({
    mutationFn: ({ hotspotIds }: { hotspotIds: number[]; targetClusterId: number }) =>
      clustersApi.split(selectedClusterId!, { hotspot_ids: hotspotIds }),
    onSuccess: async (_, variables) => {
      // 拆分后，将热点合并到目标聚簇
      if (variables.targetClusterId) {
        const newClusterId = await clustersApi.list().then(res =>
          res.items.find(c => !clustersData?.items.find(old => old.id === c.id))?.id
        );
        if (newClusterId) {
          await clustersApi.merge({
            source_cluster_ids: [newClusterId, variables.targetClusterId]
          });
        }
      }
      message.success("热点移动成功");
      setMoveHotspotModalVisible(false);
      setSelectedHotspotIds([]);
      setTargetClusterId(null);
      queryClient.invalidateQueries({ queryKey: ["cluster-hotspots", selectedClusterId] });
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`移动失败: ${error.message}`);
    }
  });

  // 创建聚簇
  const createClusterMutation = useMutation({
    mutationFn: clustersApi.create,
    onSuccess: () => {
      message.success("聚簇创建成功");
      setCreateClusterModalVisible(false);
      setCreateClusterName("");
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`创建失败: ${error.message}`);
    }
  });

  // 构建树形数据 - 重新设计聚簇项样式
  const treeData: DataNode[] =
    filteredClusters.map((cluster: ClusterInfo) => {
      // 统计各状态的数量
      const statusCounts = cluster.statuses.reduce((acc, status) => {
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      // 检查是否所有热点都是"已过滤"状态
      const allFiltered = cluster.statuses.length > 0 &&
        cluster.statuses.every(status => status === 'filtered');

      // 格式化时间
      const updateTime = new Date(cluster.last_hotspot_update).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });

      return {
        key: `cluster-${cluster.id}`,
        title: (
          <div style={{ padding: '4px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
              <span style={{ fontWeight: 500 }}>
                {cluster.cluster_name}
              </span>
              <span style={{ marginLeft: 8, color: '#666', fontSize: 12 }}>
                ({cluster.member_count})
              </span>
              {allFiltered && (
                <Tag color="orange" style={{ marginLeft: 8, fontSize: 11, padding: '0 4px', height: 18, lineHeight: '18px' }}>
                  已过滤
                </Tag>
              )}
            </div>
            {/* 状态统计 */}
            <div style={{ marginBottom: 4 }}>
              <Space size={4}>
                {Object.entries(statusCounts).map(([status, count]) => {
                  const statusInfo = STATUS_MAP[status as keyof typeof STATUS_MAP];
                  return statusInfo ? (
                    <Tag
                      key={status}
                      color={statusInfo.color}
                      style={{ fontSize: 10, padding: '0 4px', height: 16, lineHeight: '16px', margin: 0 }}
                    >
                      {statusInfo.label}: {count}
                    </Tag>
                  ) : null;
                })}
              </Space>
            </div>
            <div style={{ fontSize: 11, color: '#999' }}>
              {updateTime}
            </div>
          </div>
        ),
        isLeaf: false,
        cluster
      };
    }) || [];

  // 选中聚簇
  const handleSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length > 0) {
      const key = selectedKeys[0] as string;
      if (key.startsWith("cluster-")) {
        const clusterId = parseInt(key.replace("cluster-", ""));
        setSelectedClusterId(clusterId);
      }
    }
  };

  // 查看热点详情
  const handleViewHotspot = async (hotspot: HotspotDetail) => {
    setSelectedHotspot(hotspot);
    setHotspotDetailVisible(true);
  };

  // 删除聚簇
  const handleDeleteCluster = () => {
    if (!selectedClusterId) return;
    Modal.confirm({
      title: "确认删除",
      content: "确定要删除该聚簇吗？聚簇下的所有热点将被解除关联。",
      onOk: () => deleteClusterMutation.mutate(selectedClusterId)
    });
  };

  // 重命名聚簇
  const handleRenameCluster = () => {
    if (!selectedClusterId) return;
    const cluster = clustersData?.items.find((c: ClusterInfo) => c.id === selectedClusterId);
    if (cluster) {
      setNewClusterName(cluster.cluster_name);
      setRenameModalVisible(true);
    }
  };

  // 创建聚簇
  const handleCreateCluster = () => {
    if (!createClusterName.trim()) {
      message.warning("请输入聚簇名称");
      return;
    }
    createClusterMutation.mutate({
      cluster_name: createClusterName.trim()
    });
  };

  // 删除热点
  const handleDeleteHotspot = (hotspotId: number) => {
    Modal.confirm({
      title: "确认删除",
      content: "确定要删除该热点吗？",
      onOk: () => deleteHotspotMutation.mutate(hotspotId)
    });
  };

  // 合并聚簇
  const handleMergeClusters = () => {
    if (selectedClusters.length < 2) {
      message.warning("请至少选择2个聚簇进行合并");
      return;
    }
    mergeClustersMutation.mutate({
      source_cluster_ids: selectedClusters
    });
  };

  // 移动热点到聚簇
  const handleMoveHotspots = () => {
    if (selectedHotspotIds.length === 0) {
      message.warning("请至少选择一个热点");
      return;
    }
    if (!targetClusterId) {
      message.warning("请选择目标聚簇");
      return;
    }
    moveHotspotMutation.mutate({
      hotspotIds: selectedHotspotIds,
      targetClusterId
    });
  };

  // 热点表格行选择配置
  const rowSelection = {
    selectedRowKeys: selectedHotspotIds,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedHotspotIds(selectedRowKeys as number[]);
    }
  };

  // 热点表格列
  const columns = [
    {
      title: "关键词",
      dataIndex: "keyword",
      key: "keyword",
      width: 200,
      render: (text: string, record: HotspotDetail) => (
        <a onClick={() => handleViewHotspot(record)}>{text}</a>
      )
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: string) => {
        const statusInfo = STATUS_MAP[status as keyof typeof STATUS_MAP];
        return statusInfo ? (
          <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
        ) : (
          <Tag>{status}</Tag>
        );
      }
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
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: "最后出现",
      dataIndex: "last_seen_at",
      key: "last_seen_at",
      width: 180,
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: "操作",
      key: "actions",
      width: 100,
      render: (_: any, record: HotspotDetail) => (
        <Space>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteHotspot(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  const selectedCluster = clustersData?.items.find(
    (c: ClusterInfo) => c.id === selectedClusterId
  );

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", gap: 16, height: "calc(100vh - 150px)" }}>
        {/* 左侧：聚簇树 */}
        <Card
          title="热点聚簇"
          style={{ width: 380, overflow: "auto" }}
          extra={
            <Space>
              <Button
                icon={<PlusOutlined />}
                size="small"
                onClick={() => setCreateClusterModalVisible(true)}
                title="新建聚簇"
              />
              <Button
                icon={<MergeCellsOutlined />}
                size="small"
                onClick={() => setMergeModalVisible(true)}
                title="合并聚簇"
              />
              <Button
                icon={<ReloadOutlined />}
                size="small"
                onClick={() => refetchClusters()}
              />
            </Space>
          }
        >
          <div style={{ marginBottom: 12 }}>
            <Input.Search
              placeholder="搜索聚簇（相似度搜索）..."
              allowClear
              value={clusterSearchKeyword}
              onChange={(e) => setClusterSearchKeyword(e.target.value)}
              loading={clustersLoading}
              style={{ width: '100%' }}
            />
          </div>

          {/* 过滤器 */}
          <div style={{ marginBottom: 12, display: 'flex', gap: 8, flexDirection: 'column' }}>
            <Dropdown
              trigger={['click']}
              menu={{
                items: [],
                // 使用自定义渲染
              }}
              dropdownRender={() => (
                <div style={{ background: '#fff', borderRadius: 4, boxShadow: '0 2px 8px rgba(0,0,0,0.15)', padding: 12, minWidth: 200 }}>
                  <div style={{ marginBottom: 8, fontWeight: 500, fontSize: 12 }}>按状态过滤</div>
                  <Checkbox.Group
                    value={filterStatusList}
                    onChange={(values) => setFilterStatusList(values as string[])}
                    style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
                  >
                    {Object.entries(STATUS_MAP).map(([key, value]) => (
                      <Checkbox key={key} value={key}>
                        <Tag color={value.color} style={{ fontSize: 11, margin: 0 }}>
                          {value.label}
                        </Tag>
                      </Checkbox>
                    ))}
                  </Checkbox.Group>
                  <div style={{ marginTop: 8, display: 'flex', gap: 4 }}>
                    <Button size="small" onClick={() => setFilterStatusList([])}>清除</Button>
                  </div>
                </div>
              )}
            >
              <Button
                icon={<FilterOutlined />}
                size="small"
                style={{ width: '100%' }}
              >
                状态过滤 {filterStatusList.length > 0 && `(${filterStatusList.length})`}
              </Button>
            </Dropdown>

            <DatePicker.RangePicker
              size="small"
              placeholder={['开始时间', '结束时间']}
              style={{ width: '100%' }}
              value={filterDateRange}
              onChange={(dates) => setFilterDateRange(dates)}
              showTime={{ format: 'HH:mm' }}
              format="YYYY-MM-DD HH:mm"
            />
          </div>

          <Tree
            showLine={false}
            showIcon={false}
            selectable
            treeData={treeData}
            onSelect={handleSelect}
            selectedKeys={selectedClusterId ? [`cluster-${selectedClusterId}`] : []}
          />
        </Card>

        {/* 右侧：热点列表 */}
        <Card
          title={selectedCluster ? `${selectedCluster.cluster_name} - 热点列表` : "请选择聚簇"}
          style={{ flex: 1, overflow: "auto" }}
          extra={
            selectedClusterId && (
              <Space>
                {selectedHotspotIds.length > 0 && (
                  <Button
                    icon={<SwapOutlined />}
                    size="small"
                    onClick={() => setMoveHotspotModalVisible(true)}
                  >
                    移动到聚簇
                  </Button>
                )}
                <Button
                  icon={<EditOutlined />}
                  size="small"
                  onClick={handleRenameCluster}
                >
                  重命名
                </Button>
                <Button
                  icon={<DeleteOutlined />}
                  size="small"
                  danger
                  onClick={handleDeleteCluster}
                  loading={deleteClusterMutation.isPending}
                >
                  删除聚簇
                </Button>
              </Space>
            )
          }
        >
          {selectedClusterId ? (
            <Table
              rowSelection={rowSelection}
              columns={columns}
              dataSource={hotspotsData?.items || []}
              rowKey="id"
              loading={hotspotsLoading}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`
              }}
            />
          ) : (
            <div style={{ textAlign: "center", padding: "60px 0", color: "#999" }}>
              请从左侧选择一个聚簇查看热点
            </div>
          )}
        </Card>
      </div>

      {/* 合并聚簇弹窗 */}
      <Modal
        title="合并聚簇"
        open={mergeModalVisible}
        onOk={handleMergeClusters}
        onCancel={() => {
          setMergeModalVisible(false);
          setSelectedClusters([]);
        }}
        okText="合并"
        cancelText="取消"
        confirmLoading={mergeClustersMutation.isPending}
      >
        <p>请选择要合并的聚簇（至少选择2个）：</p>
        <div style={{ maxHeight: 400, overflowY: "auto" }}>
          {clustersData?.items.map((cluster) => (
            <div key={cluster.id} style={{ marginBottom: 8 }}>
              <Checkbox
                checked={selectedClusters.includes(cluster.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedClusters([...selectedClusters, cluster.id]);
                  } else {
                    setSelectedClusters(selectedClusters.filter((id) => id !== cluster.id));
                  }
                }}
              >
                {cluster.cluster_name} ({cluster.member_count} 个热点)
              </Checkbox>
            </div>
          ))}
        </div>
      </Modal>

      {/* 移动热点到聚簇弹窗 */}
      <Modal
        title="移动热点到聚簇"
        open={moveHotspotModalVisible}
        onOk={handleMoveHotspots}
        onCancel={() => {
          setMoveHotspotModalVisible(false);
          setTargetClusterId(null);
        }}
        okText="移动"
        cancelText="取消"
        confirmLoading={moveHotspotMutation.isPending}
      >
        <p>已选择 {selectedHotspotIds.length} 个热点，请选择目标聚簇：</p>
        <Select
          style={{ width: "100%" }}
          placeholder="选择目标聚簇"
          value={targetClusterId}
          onChange={setTargetClusterId}
        >
          {clustersData?.items
            .filter((c) => c.id !== selectedClusterId)
            .map((cluster) => (
              <Select.Option key={cluster.id} value={cluster.id}>
                {cluster.cluster_name} ({cluster.member_count} 个热点)
              </Select.Option>
            ))}
        </Select>
      </Modal>

      {/* 创建聚簇弹窗 */}
      <Modal
        title="创建新聚簇"
        open={createClusterModalVisible}
        onOk={handleCreateCluster}
        onCancel={() => {
          setCreateClusterModalVisible(false);
          setCreateClusterName("");
        }}
        okText="创建"
        cancelText="取消"
        confirmLoading={createClusterMutation.isPending}
      >
        <p>请输入新聚簇的名称：</p>
        <Input
          placeholder="聚簇名称"
          value={createClusterName}
          onChange={(e) => setCreateClusterName(e.target.value)}
          onPressEnter={handleCreateCluster}
        />
      </Modal>

      {/* 热点详情抽屉 */}
      <Drawer
        title="热点详情"
        placement="right"
        width={720}
        open={hotspotDetailVisible}
        onClose={() => {
          setHotspotDetailVisible(false);
          setSelectedHotspot(null);
        }}
      >
        {selectedHotspot && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="关键词">{selectedHotspot.keyword}</Descriptions.Item>
            <Descriptions.Item label="标准化关键词">
              {selectedHotspot.normalized_keyword}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_MAP[selectedHotspot.status]?.color}>
                {STATUS_MAP[selectedHotspot.status]?.label || selectedHotspot.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="聚簇ID">{selectedHotspot.cluster_id}</Descriptions.Item>
            <Descriptions.Item label="出现次数">
              {selectedHotspot.appearance_count}
            </Descriptions.Item>
            <Descriptions.Item label="首次出现">
              {new Date(selectedHotspot.first_seen_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="最后出现">
              {new Date(selectedHotspot.last_seen_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="向量模型">
              {selectedHotspot.embedding_model}
            </Descriptions.Item>
            <Descriptions.Item label="是否过滤">
              {selectedHotspot.is_filtered ? <Tag color="red">是</Tag> : <Tag color="green">否</Tag>}
            </Descriptions.Item>
            {selectedHotspot.filter_reason && (
              <Descriptions.Item label="过滤原因">
                {selectedHotspot.filter_reason}
              </Descriptions.Item>
            )}
            {selectedHotspot.filtered_at && (
              <Descriptions.Item label="过滤时间">
                {new Date(selectedHotspot.filtered_at).toLocaleString()}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="爬取次数">{selectedHotspot.crawl_count}</Descriptions.Item>
            {selectedHotspot.last_crawled_at && (
              <Descriptions.Item label="最后爬取时间">
                {new Date(selectedHotspot.last_crawled_at).toLocaleString()}
              </Descriptions.Item>
            )}
            {selectedHotspot.crawl_failed_count > 0 && (
              <Descriptions.Item label="爬取失败次数">
                {selectedHotspot.crawl_failed_count}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="平台信息">
              {selectedHotspot.platforms.map((platform, index) => (
                <div key={index} style={{ marginBottom: 8 }}>
                  <Tag color="blue">{platform.platform}</Tag>
                  排名: {platform.rank} | 热度: {platform.heat_score}
                  <br />
                  时间: {new Date(platform.seen_at).toLocaleString()}
                </div>
              ))}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedHotspot.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedHotspot.updated_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* 重命名聚簇弹窗 */}
      <Modal
        title="重命名聚簇"
        open={renameModalVisible}
        onOk={() => {
          if (selectedClusterId && newClusterName.trim()) {
            renameClusterMutation.mutate({
              clusterId: selectedClusterId,
              clusterName: newClusterName.trim()
            });
          }
        }}
        onCancel={() => {
          setRenameModalVisible(false);
          setNewClusterName("");
        }}
        confirmLoading={renameClusterMutation.isPending}
      >
        <Input
          placeholder="请输入新的聚簇名称"
          value={newClusterName}
          onChange={(e) => setNewClusterName(e.target.value)}
        />
      </Modal>
    </div>
  );
}

export default Hotspots;
