import { Space, Input, Select, DatePicker, Button } from "antd";
import {
  SearchOutlined,
  FilterOutlined,
  CheckCircleOutlined
} from "@ant-design/icons";
import type { Dayjs } from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";

const { RangePicker } = DatePicker;

interface HotspotsFilterProps {
  searchKeyword: string;
  filterStatus: string[];
  excludeStatus: string[];
  filterPlatforms: string[];
  excludePlatforms: string[];
  filterDateRange: [Dayjs | null, Dayjs | null] | null;
  onSearchChange: (value: string) => void;
  onStatusChange: (values: string[]) => void;
  onExcludeStatusChange: (values: string[]) => void;
  onPlatformsChange: (values: string[]) => void;
  onExcludePlatformsChange: (values: string[]) => void;
  onDateRangeChange: (dates: [Dayjs | null, Dayjs | null] | null) => void;
  onReset: () => void;
  onQuickFilterPendingValidation: () => void;
}

export function HotspotsFilter({
  searchKeyword,
  filterStatus,
  excludeStatus,
  filterPlatforms,
  excludePlatforms,
  filterDateRange,
  onSearchChange,
  onStatusChange,
  onExcludeStatusChange,
  onPlatformsChange,
  onExcludePlatformsChange,
  onDateRangeChange,
  onReset,
  onQuickFilterPendingValidation
}: HotspotsFilterProps) {
  return (
    <Space style={{ marginBottom: 16 }} wrap>
      <Input
        placeholder="搜索聚簇名称或关键词"
        prefix={<SearchOutlined />}
        value={searchKeyword}
        onChange={(e) => onSearchChange(e.target.value)}
        style={{ width: 250 }}
        allowClear
      />

      <Select
        mode="multiple"
        placeholder="排除状态（反选）"
        value={excludeStatus}
        onChange={onExcludeStatusChange}
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
        placeholder="选择状态"
        value={filterStatus}
        onChange={onStatusChange}
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
        onChange={onPlatformsChange}
        style={{ width: 250 }}
        maxTagCount="responsive"
      >
        {Object.entries(PLATFORM_MAP).map(([value, label]) => (
          <Select.Option key={value} value={value}>
            {label}
          </Select.Option>
        ))}
      </Select>

      <Select
        mode="multiple"
        placeholder="排除平台（反选）"
        value={excludePlatforms}
        onChange={onExcludePlatformsChange}
        style={{ width: 250 }}
        allowClear
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
        onChange={onDateRangeChange}
        showTime
        format="YYYY-MM-DD HH:mm"
        placeholder={["开始时间", "结束时间"]}
      />

      <Button
        type="primary"
        icon={<CheckCircleOutlined />}
        onClick={onQuickFilterPendingValidation}
      >
        待审核热词
      </Button>

      <Button icon={<FilterOutlined />} onClick={onReset}>
        重置过滤
      </Button>
    </Space>
  );
}
