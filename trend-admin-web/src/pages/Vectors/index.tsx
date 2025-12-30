import {
  Card,
  Form,
  Input,
  Button,
  message,
  Space,
  Modal,
  Typography,
  Empty,
  Popconfirm,
  Tooltip,
  Tag,
  Drawer,
  InputNumber,
  Slider,
  Divider,
  Select,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  DeleteOutlined,
  FolderOutlined,
  FileTextOutlined,
  SettingOutlined,
  CloseOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { vectorsApi } from '@/api/vectors';
import type { VectorInfo, CollectionInfo, VectorSearchResult } from '@/types/api';
import './styles.css';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

function Vectors() {
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [searchDrawerVisible, setSearchDrawerVisible] = useState(false);
  const [addForm] = Form.useForm();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchThreshold, setSearchThreshold] = useState<number>(0.7);
  const [searchTopK, setSearchTopK] = useState<number>(10);
  const [searchCollectionFilter, setSearchCollectionFilter] = useState<string | undefined>(
    undefined
  );
  const [searchResults, setSearchResults] = useState<VectorSearchResult[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  // 获取集合列表
  const {
    data: collectionsData,
    isLoading: collectionsLoading,
    refetch: refetchCollections,
  } = useQuery({
    queryKey: ['vector-collections'],
    queryFn: vectorsApi.listCollections,
  });

  const collections = collectionsData?.collections || [];

  // 添加向量
  const addMutation = useMutation({
    mutationFn: vectorsApi.add,
    onSuccess: (data) => {
      message.success(`向量添加成功！ID: ${data.vector_id}`);
      addForm.resetFields();
      setAddModalVisible(false);
      refetchCollections();
    },
    onError: (error: any) => {
      message.error(`添加失败: ${error.message}`);
    },
  });

  // 删除向量
  const deleteMutation = useMutation({
    mutationFn: vectorsApi.delete,
    onSuccess: (data) => {
      message.success(data.message);
      refetchCollections();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    },
  });

  // 删除集合
  const deleteCollectionMutation = useMutation({
    mutationFn: vectorsApi.deleteCollection,
    onSuccess: (data) => {
      message.success(data.message);
      if (selectedCollection === data.message.split("'")[1]) {
        setSelectedCollection(null);
      }
      refetchCollections();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    },
  });

  const handleAdd = async () => {
    try {
      const values = await addForm.validateFields();
      let metadata = undefined;

      if (values.metadata) {
        try {
          metadata = JSON.parse(values.metadata);
        } catch (err) {
          message.error('元数据格式错误，请输入有效的 JSON');
          return;
        }
      }

      addMutation.mutate({
        text: values.text,
        collection_id: values.collection_id,
        metadata,
      });
    } catch (err) {
      // 表单验证失败
    }
  };

  const handleDeleteVector = (vectorId: number) => {
    deleteMutation.mutate(vectorId);
  };

  const handleDeleteCollection = (collectionId: string) => {
    deleteCollectionMutation.mutate(collectionId);
  };

  // 搜索向量
  const searchMutation = useMutation({
    mutationFn: vectorsApi.search,
    onSuccess: (data) => {
      setSearchResults(data.results);
      setSearchDrawerVisible(true);
      message.success(`找到 ${data.count} 条相似结果`);
    },
    onError: (error: any) => {
      message.error(`搜索失败: ${error.message}`);
    },
  });

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    searchMutation.mutate({
      query_text: searchQuery,
      collection_id: searchCollectionFilter,
      top_k: searchTopK,
      threshold: searchThreshold,
    });
  };

  // 获取当前选中集合的向量列表
  const currentVectors =
    collections.find((c: CollectionInfo) => c.collection_id === selectedCollection)?.vectors ||
    [];

  return (
    <div className="vectors-container">
      {/* 顶部搜索栏 */}
      <div className="vectors-header">
        <Space.Compact style={{ maxWidth: 500 }}>
          <Input
            placeholder="语义搜索向量内容..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            prefix={<SearchOutlined />}
          />
          <Tooltip title="执行搜索">
            <Button
              icon={<SettingOutlined />}
              onClick={handleSearch}
              loading={searchMutation.isPending}
            >
              搜索
            </Button>
          </Tooltip>
        </Space.Compact>
        <Space>
          <Select
            placeholder="全部集合"
            value={searchCollectionFilter}
            onChange={setSearchCollectionFilter}
            style={{ width: 180 }}
            allowClear
            suffixIcon={<FilterOutlined />}
            options={[
              { label: '全部集合', value: undefined },
              ...collections.map((c: CollectionInfo) => ({
                label: `${c.collection_id} (${c.count})`,
                value: c.collection_id,
              })),
            ]}
          />
          <Tooltip title={`相似度阈值: ${(searchThreshold * 100).toFixed(0)}%`}>
            <Slider
              min={0}
              max={1}
              step={0.05}
              value={searchThreshold}
              onChange={setSearchThreshold}
              style={{ width: 120 }}
              tooltip={{ formatter: (value) => `${((value || 0) * 100).toFixed(0)}%` }}
            />
          </Tooltip>
          <InputNumber
            min={1}
            max={50}
            value={searchTopK}
            onChange={(val) => setSearchTopK(val || 10)}
            style={{ width: 80 }}
            prefix="Top"
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddModalVisible(true)}
          >
            添加向量
          </Button>
        </Space>
      </div>

      {/* 主体区域 */}
      <div className="vectors-content">
        {/* 左侧：Collection 列表 */}
        <div className="collections-sidebar">
          <div className="collections-header">
            <Text strong>集合列表</Text>
            <Text type="secondary">{collections.length} 个</Text>
          </div>
          <div className="collections-list">
            {collectionsLoading ? (
              <div style={{ padding: 20, textAlign: 'center' }}>
                <Text type="secondary">加载中...</Text>
              </div>
            ) : collections.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无集合"
                style={{ padding: 20 }}
              />
            ) : (
              collections.map((collection: CollectionInfo) => (
                <div
                  key={collection.collection_id}
                  className={`collection-item ${
                    selectedCollection === collection.collection_id ? 'active' : ''
                  }`}
                  onClick={() => setSelectedCollection(collection.collection_id)}
                >
                  <div className="collection-info">
                    <FolderOutlined className="collection-icon" />
                    <div className="collection-text">
                      <Text ellipsis className="collection-name">
                        {collection.collection_id}
                      </Text>
                      <Text type="secondary" className="collection-count">
                        {collection.count} 个向量
                      </Text>
                    </div>
                  </div>
                  <Popconfirm
                    title="确认删除"
                    description={`确定要删除集合 "${collection.collection_id}" 及其所有向量吗？`}
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDeleteCollection(collection.collection_id);
                    }}
                    okText="确定"
                    cancelText="取消"
                    okButtonProps={{ danger: true }}
                  >
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                      loading={deleteCollectionMutation.isPending}
                    />
                  </Popconfirm>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 右侧：向量卡片列表 */}
        <div className="vectors-main">
          {!selectedCollection ? (
            <div className="empty-state">
              <Empty description="请选择一个集合查看向量数据" />
            </div>
          ) : currentVectors.length === 0 ? (
            <div className="empty-state">
              <Empty description="该集合暂无向量数据" />
            </div>
          ) : (
            <div className="vectors-grid">
              {currentVectors.map((vector: VectorInfo) => (
                <Card
                  key={vector.id}
                  className="vector-card"
                  hoverable
                  actions={[
                    <Popconfirm
                      key="delete"
                      title="确认删除"
                      description="确定要删除这个向量吗？"
                      onConfirm={() => handleDeleteVector(vector.id)}
                      okText="确定"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        loading={deleteMutation.isPending}
                      >
                        删除
                      </Button>
                    </Popconfirm>,
                  ]}
                >
                  <div className="vector-header">
                    <FileTextOutlined className="vector-icon" />
                    <Text type="secondary" className="vector-id">
                      ID: {vector.id}
                    </Text>
                  </div>
                  <Paragraph
                    ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                    className="vector-content"
                  >
                    {vector.content || '(无内容)'}
                  </Paragraph>
                  {vector.metadata && (
                    <div className="vector-metadata">
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        元数据:
                      </Text>
                      <Tooltip title={JSON.stringify(vector.metadata, null, 2)}>
                        <Tag color="blue" style={{ marginLeft: 8 }}>
                          {Object.keys(vector.metadata).length} 个字段
                        </Tag>
                      </Tooltip>
                    </div>
                  )}
                  <Text type="secondary" className="vector-time">
                    {new Date(vector.createtime).toLocaleString('zh-CN')}
                  </Text>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 添加向量弹窗 */}
      <Modal
        title="添加向量"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          addForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form form={addForm} layout="vertical" onFinish={handleAdd}>
          <Form.Item
            label="集合 ID"
            name="collection_id"
            rules={[{ required: true, message: '请输入集合 ID' }]}
          >
            <Input placeholder="例如: my-collection" />
          </Form.Item>
          <Form.Item
            label="文本内容"
            name="text"
            rules={[{ required: true, message: '请输入文本内容' }]}
          >
            <TextArea rows={6} placeholder="输入要向量化的文本..." />
          </Form.Item>
          <Form.Item label="元数据 (JSON)" name="metadata">
            <TextArea
              rows={3}
              placeholder='例如: {"author": "张三", "title": "文章标题"}'
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setAddModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={addMutation.isPending}>
                添加
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 搜索结果抽屉 */}
      <Drawer
        title={
          <Space>
            <SearchOutlined />
            <span>搜索结果</span>
            <Tag color="blue">{searchResults.length} 条</Tag>
          </Space>
        }
        placement="right"
        width={480}
        open={searchDrawerVisible}
        onClose={() => setSearchDrawerVisible(false)}
        closeIcon={<CloseOutlined />}
      >
        {searchResults.length === 0 ? (
          <Empty description="暂无搜索结果" />
        ) : (
          <div className="search-results-list">
            {searchResults.map((result, index) => (
              <Card
                key={result.id}
                className="search-result-card"
                size="small"
                style={{ marginBottom: 12 }}
              >
                <div className="search-result-header">
                  <Space>
                    <Text strong>#{index + 1}</Text>
                    <Tag color="green">
                      {(result.similarity * 100).toFixed(1)}% 相似
                    </Tag>
                    <Tag color="blue">{result.collection_id}</Tag>
                  </Space>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    ID: {result.id}
                  </Text>
                </div>
                <Divider style={{ margin: '8px 0' }} />
                <Paragraph
                  ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}
                  style={{ marginBottom: 8, fontSize: 13 }}
                >
                  {result.content || '(无内容)'}
                </Paragraph>
                {result.metadata && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      元数据:{' '}
                    </Text>
                    <Tooltip title={JSON.stringify(result.metadata, null, 2)}>
                      <Tag color="purple" style={{ fontSize: 11 }}>
                        {Object.keys(result.metadata).length} 个字段
                      </Tag>
                    </Tooltip>
                  </div>
                )}
                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 8 }}>
                  {new Date(result.createtime).toLocaleString('zh-CN')}
                </Text>
              </Card>
            ))}
          </div>
        )}
      </Drawer>
    </div>
  );
}

export default Vectors;
