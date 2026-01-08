import {
  Card,
  Table,
  Space,
  Button,
  message,
  Tag,
  Input,
  Select,
  DatePicker,
  Tooltip,
  Drawer,
  Descriptions,
  Modal,
  Form,
} from 'antd';
import {
  ReloadOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clustersApi } from '@/api/clusters';
import { hotspotsApi } from '@/api/hotspots';
import type { ClusterInfo, HotspotDetail } from '@/types/api';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

// 状态映射
const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_validation: { label: '待验证', color: 'orange' },
  validated: { label: '已验证', color: 'green' },
  rejected: { label: '已拒绝', color: 'red' },
  crawling: { label: '爬取中', color: 'blue' },
  crawled: { label: '已爬取', color: 'cyan' },
  analyzing: { label: '分析中', color: 'purple' },
  analyzed: { label: '已分析', color: 'geekblue' },
  archived: { label: '已归档', color: 'default' },
  outdated: { label: '已过时', color: 'volcano' },
};

// 平台映射
const PLATFORM_MAP: Record<string, string> = {
  xhs: '小红书',
  dy: '抖音',
  bili: '哔哩哔哩',
  weibo: '微博',
  ks: '快手',
  tieba: '贴吧',
  zhihu: '知乎',
};

function Hotspots() {
  const queryClient = useQueryClient();
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([]);
  
  // 过滤条件状态
  const [filterStatus, setFilterStatus] = useState<string[]>([]);
  const [excludeStatus, setExcludeStatus] = useState<string[]>([]);
  const [filterPlatforms, setFilterPlatforms] = useState<string[]>([]);
  const [filterDateRange, setFilterDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [searchKeyword, setSearchKeyword] = useState<string>('');

  // 详情抽屉状态
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(null);

  // 编辑聚簇名称
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<ClusterInfo | null>(null);
  const [form] = Form.useForm();

  // 查询聚簇列表
  const {
    data: clustersData,
    isLoading: clustersLoading,
    refetch: refetchClusters,
  } = useQuery({
    queryKey: ['clusters', filterStatus, excludeStatus, filterPlatforms, filterDateRange],
    queryFn: async () => {
      const params: any = {};
      if (filterStatus.length > 0) params.status = filterStatus.join(',');
      if (excludeStatus.length > 0) params.exclude_status = excludeStatus.join(',');
      if (filterPlatforms.length > 0) params.platforms = filterPlatforms.join(',');
      if (filterDateRange?.[0]) params.start_time = filterDateRange[0].toISOString();
      if (filterDateRange?.[1]) params.end_time = filterDateRange[1].toISOString();
      
      return clustersApi.list(params);
    },
  });

  // 查询聚簇下的热点
  const getClusterHotspots = async (clusterId: number) => {
    return hotspotsApi.getClusterHotspots(clusterId);
  };

  // 更新聚簇名称
  const updateClusterMutation = useMutation({
    mutationFn: ({ clusterId, clusterName }: { clusterId: number; clusterName: string }) =>
      clustersApi.update(clusterId, { cluster_name: clusterName }),
    onSuccess: () => {
      message.success('聚簇名称更新成功');
      setEditModalVisible(false);
      setEditingCluster(null);
      form.resetFields();
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message}`);
    },
  });

  // 删除聚簇
  const deleteClusterMutation = useMutation({
    mutationFn: (clusterId: number) => clustersApi.delete(clusterId),
    onSuccess: () => {
      message.success('聚簇删除成功');
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    },
  });

  // 删除热点
  const deleteHotspotMutation = useMutation({
    mutationFn: (hotspotId: number) => hotspotsApi.delete(hotspotId),
    onSuccess: () => {
      message.success('热点删除成功');
      queryClient.invalidateQueries({ queryKey: ['clusterHotspots'] });
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    },
  });

  // 主表格列定义（聚簇）
  const clusterColumns: ColumnsType<ClusterInfo> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '聚簇名称',
      dataIndex: 'cluster_name',
      key: 'cluster_name',
      width: 200,
      filteredValue: searchKeyword ? [searchKeyword] : null,
      onFilter: (value, record) => {
        const keyword = value as string;
        return (
          record.cluster_name.toLowerCase().includes(keyword.toLowerCase()) ||
          record.keywords.some((k) => k.toLowerCase().includes(keyword.toLowerCase()))
        );
      },
    },
    {
      title: '热点数量',
      dataIndex: 'member_count',
      key: 'member_count',
      width: 150,
      sorter: (a, b) => a.member_count - b.member_count,
    },
    {
      title: '平台分布',
      dataIndex: 'platforms',
      key: 'platforms',
      width: 250,
      render: (platforms: ClusterInfo['platforms']) => (
        <Space size={4} wrap>
          {platforms.map((p) => (
            <Tag key={p.platform} color="blue">
              {PLATFORM_MAP[p.platform] || p.platform} ({p.count})
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'statuses',
      key: 'statuses',
      width: 200,
      render: (statuses: string[]) => (
        <Space size={4} wrap>
          {statuses.map((status, idx) => {
            const statusInfo = STATUS_MAP[status];
            return (
              <Tag key={idx} color={statusInfo?.color || 'default'}>
                {statusInfo?.label || status}
              </Tag>
            );
          })}
        </Space>
      ),
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      width: 250,
      ellipsis: { showTitle: false },
      render: (keywords: string[]) => (
        <Tooltip title={keywords.join(', ')}>
          <span>{keywords.slice(0, 3).join(', ')}{keywords.length > 3 ? '...' : ''}</span>
        </Tooltip>
      ),
    },
    {
      title: '最后更新',
      dataIndex: 'last_hotspot_update',
      key: 'last_hotspot_update',
      width: 180,
      sorter: (a, b) =>
        new Date(a.last_hotspot_update).getTime() - new Date(b.last_hotspot_update).getTime(),
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                setEditingCluster(record);
                form.setFieldsValue({ cluster_name: record.cluster_name });
                setEditModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                Modal.confirm({
                  title: '确认删除',
                  content: `确定要删除聚簇"${record.cluster_name}"吗？`,
                  onOk: () => deleteClusterMutation.mutate(record.id),
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 展开的子表格列定义（热点）
  const hotspotColumns: ColumnsType<HotspotDetail> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '关键词',
      dataIndex: 'keyword',
      key: 'keyword',
      width: 200,
    },
    {
      title: '标准化关键词',
      dataIndex: 'normalized_keyword',
      key: 'normalized_keyword',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const statusInfo = STATUS_MAP[status];
        return (
          <Tag color={statusInfo?.color || 'default'}>
            {statusInfo?.label || status}
          </Tag>
        );
      },
    },
    {
      title: '平台',
      dataIndex: 'platforms',
      key: 'platforms',
      width: 200,
      render: (platforms: HotspotDetail['platforms']) => (
        <Space size={4} wrap>
          {platforms.map((p, idx) => (
            <Tag key={idx} color="blue">
              {PLATFORM_MAP[p.platform] || p.platform}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '出现次数',
      dataIndex: 'appearance_count',
      key: 'appearance_count',
      width: 100,
    },
    {
      title: '首次出现',
      dataIndex: 'first_seen_at',
      key: 'first_seen_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedHotspot(record);
                setDetailDrawerVisible(true);
              }}
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
                  title: '确认删除',
                  content: `确定要删除热点"${record.keyword}"吗？`,
                  onOk: () => deleteHotspotMutation.mutate(record.id),
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 展开行渲染 - 使用缓存的热点数据
  const renderExpandedRow = (record: ClusterInfo) => {
    const hotspotsData = queryClient.getQueryData<any>(['clusterHotspots', record.id]);
    return (
      <Table
        columns={hotspotColumns}
        dataSource={hotspotsData?.items || []}
        rowKey="id"
        size="small"
        pagination={false}
        loading={!hotspotsData}
      />
    );
  };

  // 处理展开/收起
  const handleExpand = async (expanded: boolean, record: ClusterInfo) => {
    if (expanded) {
      setExpandedRowKeys([...expandedRowKeys, record.id]);
      try {
        const data = await getClusterHotspots(record.id);
        // 缓存数据到 react-query
        queryClient.setQueryData(['clusterHotspots', record.id], data);
      } catch (error: any) {
        message.error(`加载热点数据失败: ${error.message}`);
      }
    } else {
      setExpandedRowKeys(expandedRowKeys.filter((key) => key !== record.id));
    }
  };

  // 重置过滤条件
  const handleResetFilters = () => {
    setFilterStatus([]);
    setExcludeStatus([]);
    setFilterPlatforms([]);
    setFilterDateRange(null);
    setSearchKeyword('');
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="热点聚簇管理"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchClusters()}
              loading={clustersLoading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {/* 过滤器 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索聚簇名称或关键词"
            prefix={<SearchOutlined />}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
          
          <Select
            mode="multiple"
            placeholder="选择状态"
            value={filterStatus}
            onChange={setFilterStatus}
            style={{ width: 250 }}
            allowClear
            maxTagCount="responsive"
          >
            {Object.entries(STATUS_MAP).map(([value, { label }]) => (
              <Select.Option key={value} value={value}>
                {label}
              </Select.Option>
            ))}
          </Select>

          <Select
            mode="multiple"
            placeholder="排除状态（反选）"
            value={excludeStatus}
            onChange={setExcludeStatus}
            style={{ width: 250 }}
            allowClear
            maxTagCount="responsive"
          >
            {Object.entries(STATUS_MAP).map(([value, { label }]) => (
              <Select.Option key={value} value={value}>
                {label}
              </Select.Option>
            ))}
          </Select>

          <Select
            mode="multiple"
            placeholder="选择平台"
            value={filterPlatforms}
            onChange={setFilterPlatforms}
            style={{ width: 250 }}
            maxTagCount="responsive"
          >
            {Object.entries(PLATFORM_MAP).map(([value, label]) => (
              <Select.Option key={value} value={value}>
                {label}
              </Select.Option>
            ))}
          </Select>

          <RangePicker
            value={filterDateRange}
            onChange={setFilterDateRange}
            showTime
            format="YYYY-MM-DD HH:mm"
            placeholder={['开始时间', '结束时间']}
          />

          <Button icon={<FilterOutlined />} onClick={handleResetFilters}>
            重置过滤
          </Button>
        </Space>

        {/* 主表格 */}
        <Table
          columns={clusterColumns}
          dataSource={clustersData?.items || []}
          rowKey="id"
          loading={clustersLoading}
          pagination={{
            total: clustersData?.count || 0,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个聚簇`,
          }}
          expandable={{
            expandedRowKeys,
            onExpand: handleExpand,
            expandedRowRender: renderExpandedRow,
          }}
          scroll={{ x: 1500 }}
        />
      </Card>

      {/* 热点详情抽屉 */}
      <Drawer
        title="热点详情"
        placement="right"
        width={720}
        open={detailDrawerVisible}
        onClose={() => {
          setDetailDrawerVisible(false);
          setSelectedHotspot(null);
        }}
      >
        {selectedHotspot && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="ID">{selectedHotspot.id}</Descriptions.Item>
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
              {dayjs(selectedHotspot.first_seen_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="最后出现">
              {dayjs(selectedHotspot.last_seen_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="向量模型">
              {selectedHotspot.embedding_model}
            </Descriptions.Item>
            <Descriptions.Item label="是否过滤">
              {selectedHotspot.is_filtered ? (
                <Tag color="red">是</Tag>
              ) : (
                <Tag color="green">否</Tag>
              )}
            </Descriptions.Item>
            {selectedHotspot.filter_reason && (
              <Descriptions.Item label="过滤原因">
                {selectedHotspot.filter_reason}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="爬取次数">
              {selectedHotspot.crawl_count}
            </Descriptions.Item>
            {selectedHotspot.last_crawled_at && (
              <Descriptions.Item label="最后爬取时间">
                {dayjs(selectedHotspot.last_crawled_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="平台信息">
              <Space direction="vertical">
                {selectedHotspot.platforms.map((platform, index) => (
                  <div key={index}>
                    <Tag color="blue">{PLATFORM_MAP[platform.platform] || platform.platform}</Tag>
                    <span>排名: {platform.rank}</span>
                    {platform.heat_score && <span> | 热度: {platform.heat_score}</span>}
                    <br />
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {dayjs(platform.seen_at).format('YYYY-MM-DD HH:mm:ss')}
                    </span>
                  </div>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(selectedHotspot.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {dayjs(selectedHotspot.updated_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* 编辑聚簇名称弹窗 */}
      <Modal
        title="编辑聚簇名称"
        open={editModalVisible}
        onOk={() => {
          form.validateFields().then((values) => {
            if (editingCluster) {
              updateClusterMutation.mutate({
                clusterId: editingCluster.id,
                clusterName: values.cluster_name,
              });
            }
          });
        }}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingCluster(null);
          form.resetFields();
        }}
        confirmLoading={updateClusterMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="cluster_name"
            label="聚簇名称"
            rules={[{ required: true, message: '请输入聚簇名称' }]}
          >
            <Input placeholder="请输入聚簇名称" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Hotspots;
