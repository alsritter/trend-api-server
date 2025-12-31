import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  message,
  Row,
  Col
} from "antd";
import {
  SearchOutlined,
  ReloadOutlined,
  TableOutlined,
  ApartmentOutlined
} from "@ant-design/icons";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import type {
  HotspotDetail,
  HotspotStatus,
  ListHotspotsRequest
} from "@/types/api";
import "./styles.css";
import {
  getHotspotTableColumns,
  STATUS_MAP
} from "./components/HotspotTableColumns";
import { HotspotDetailModal } from "./components/HotspotDetailModal";
import { ClusterHotspotsModal } from "./components/ClusterHotspotsModal";
import { HotspotTreeView } from "./components/HotspotTreeView";

const { Search } = Input;

function Hotspots() {
  const [viewMode, setViewMode] = useState<"tree" | "table">("tree");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<HotspotStatus | undefined>(
    undefined
  );
  const [keywordSearch, setKeywordSearch] = useState<string>("");
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(
    null
  );
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(
    null
  );

  // 查询参数
  const queryParams: ListHotspotsRequest = {
    page,
    page_size: pageSize,
    status: statusFilter,
    keyword: keywordSearch || undefined
  };

  // 获取热点列表
  const {
    data: hotspotsData,
    isLoading,
    refetch
  } = useQuery({
    queryKey: ["hotspots", queryParams],
    queryFn: () => hotspotsApi.list(queryParams)
  });

  // 删除热点
  const deleteMutation = useMutation({
    mutationFn: hotspotsApi.delete,
    onSuccess: (data) => {
      message.success(data.message);
      refetch();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 查看详情
  const handleViewDetail = async (record: HotspotDetail) => {
    setSelectedHotspot(record);
    setDetailModalVisible(true);
  };

  // 查看同簇热点
  const handleViewCluster = (clusterId: number) => {
    setSelectedClusterId(clusterId);
    setClusterModalVisible(true);
  };

  // 删除热点
  const handleDelete = (hotspotId: number) => {
    deleteMutation.mutate(hotspotId);
  };

  // 搜索
  const handleSearch = (value: string) => {
    setKeywordSearch(value);
    setPage(1);
  };

  // 重置过滤
  const handleReset = () => {
    setStatusFilter(undefined);
    setKeywordSearch("");
    setPage(1);
  };

  // 表格列定义
  const columns = getHotspotTableColumns({
    onViewDetail: handleViewDetail,
    onDelete: handleDelete,
    onViewCluster: handleViewCluster,
    isDeleting: deleteMutation.isPending
  });

  return (
    <div className="hotspots-container">
      <Row gutter={16}>
        {/* 左侧：树形视图或状态筛选 */}
        {viewMode === "tree" && (
          <Col span={6}>
            <Card title="热点聚簇" size="small">
              <HotspotTreeView
                status={statusFilter}
                onHotspotSelect={handleViewDetail}
                onRefresh={refetch}
              />
            </Card>
          </Col>
        )}

        {/* 右侧：表格或详情 */}
        <Col span={viewMode === "tree" ? 18 : 24}>
          <Card>
            {/* 顶部工具栏 */}
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Space wrap>
                {/* 视图切换按钮 */}
                <Button.Group>
                  <Button
                    icon={<ApartmentOutlined />}
                    type={viewMode === "tree" ? "primary" : "default"}
                    onClick={() => setViewMode("tree")}
                  >
                    树形视图
                  </Button>
                  <Button
                    icon={<TableOutlined />}
                    type={viewMode === "table" ? "primary" : "default"}
                    onClick={() => setViewMode("table")}
                  >
                    表格视图
                  </Button>
                </Button.Group>

                {/* 表格视图下的搜索和筛选 */}
                {viewMode === "table" && (
                  <>
                    <Search
                      placeholder="搜索热词..."
                      onSearch={handleSearch}
                      style={{ width: 300 }}
                      allowClear
                      enterButton={<SearchOutlined />}
                    />
                    <Select
                      placeholder="选择状态"
                      value={statusFilter}
                      onChange={setStatusFilter}
                      style={{ width: 150 }}
                      allowClear
                      options={[
                        { label: "全部状态", value: undefined },
                        ...Object.entries(STATUS_MAP).map(
                          ([value, { label }]) => ({
                            label,
                            value
                          })
                        )
                      ]}
                    />
                  </>
                )}

                <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                  刷新
                </Button>

                {viewMode === "table" && (
                  <Button onClick={handleReset}>重置</Button>
                )}
              </Space>
            </Space>

            {/* 数据表格 */}
            {viewMode === "table" && (
              <Table
                columns={columns}
                dataSource={hotspotsData?.items || []}
                rowKey="id"
                loading={isLoading}
                scroll={{ x: 1500 }}
                pagination={{
                  current: page,
                  pageSize: pageSize,
                  total: hotspotsData?.total || 0,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条`,
                  onChange: (newPage, newPageSize) => {
                    setPage(newPage);
                    setPageSize(newPageSize);
                  }
                }}
              />
            )}

            {/* 树形视图下显示选中热点的详情 */}
            {viewMode === "tree" && selectedHotspot && (
              <div style={{ marginTop: 16 }}>
                <h3>热点详情</h3>
                <p>关键词: {selectedHotspot.keyword}</p>
                <p>状态: {STATUS_MAP[selectedHotspot.status]?.label}</p>
                <p>出现次数: {selectedHotspot.appearance_count}</p>
                <p>首次出现: {selectedHotspot.first_seen_at}</p>
                <p>最后出现: {selectedHotspot.last_seen_at}</p>
                <Button onClick={() => setDetailModalVisible(true)}>
                  查看完整详情
                </Button>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 详情弹窗 */}
      <HotspotDetailModal
        visible={detailModalVisible}
        hotspot={selectedHotspot}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedHotspot(null);
        }}
      />

      {/* 同簇热点弹窗 */}
      <ClusterHotspotsModal
        visible={clusterModalVisible}
        clusterId={selectedClusterId}
        onClose={() => {
          setClusterModalVisible(false);
          setSelectedClusterId(null);
        }}
      />
    </div>
  );
}

export default Hotspots;
