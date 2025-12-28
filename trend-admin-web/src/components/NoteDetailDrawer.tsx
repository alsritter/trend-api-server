import { Drawer, Tabs, Spin, Empty, List, Avatar, Space, Card, Typography, Row, Col, Divider, Statistic } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { contentsApi } from '@/api/contents'
import { formatDateTime, getContentId } from '@/utils/format'
import type { Note, Comment } from '@/types/api'
import { useState } from 'react'
import { LikeOutlined, MessageOutlined, HeartOutlined, ShareAltOutlined, EyeOutlined, StarOutlined } from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

interface NoteDetailDrawerProps {
  visible: boolean
  onClose: () => void
  note: Note | null
  platform: string
}

function NoteDetailDrawer({ visible, onClose, note, platform }: NoteDetailDrawerProps) {
  const [commentPage, setCommentPage] = useState(1)
  const [commentPageSize] = useState(20)

  // 获取当前平台的内容ID
  const contentId = note ? getContentId(platform, note) : ''

  // 获取评论列表
  const { data: commentsData, isLoading: commentsLoading } = useQuery({
    queryKey: ['comments', platform, contentId, commentPage, commentPageSize],
    queryFn: () =>
      contentsApi.getComments(platform, {
        note_id: contentId,
        page: commentPage,
        page_size: commentPageSize,
      }),
    enabled: visible && !!contentId,
  })

  if (!note) return null

  // 渲染数据统计卡片
  const renderStatistics = () => {
    const stats: Array<{ label: string; value: any; icon?: React.ReactNode }> = []

    if (platform === 'xhs') {
      stats.push(
        { label: '点赞', value: note.liked_count || 0, icon: <HeartOutlined /> },
        { label: '收藏', value: note.collected_count || 0, icon: <StarOutlined /> },
        { label: '评论', value: note.comment_count || 0, icon: <MessageOutlined /> },
        { label: '分享', value: note.share_count || 0, icon: <ShareAltOutlined /> },
      )
    } else if (platform === 'dy' || platform === 'ks') {
      stats.push(
        { label: '播放', value: note.video_play_count || 0, icon: <EyeOutlined /> },
        { label: '点赞', value: note.liked_count || 0, icon: <HeartOutlined /> },
        { label: '评论', value: note.comment_count || 0, icon: <MessageOutlined /> },
        { label: '分享', value: note.video_share_count || 0, icon: <ShareAltOutlined /> },
      )
    } else if (platform === 'bili') {
      stats.push(
        { label: '播放', value: note.video_play_count || 0, icon: <EyeOutlined /> },
        { label: '弹幕', value: note.video_danmaku || 0 },
        { label: '评论', value: note.video_comment || 0, icon: <MessageOutlined /> },
        { label: '点赞', value: note.video_like_count || 0, icon: <HeartOutlined /> },
      )
    } else if (platform === 'wb') {
      stats.push(
        { label: '点赞', value: note.attitudes_count || 0, icon: <HeartOutlined /> },
        { label: '评论', value: note.comments_count || 0, icon: <MessageOutlined /> },
        { label: '转发', value: note.reposts_count || 0, icon: <ShareAltOutlined /> },
      )
    } else if (platform === 'tieba') {
      stats.push(
        { label: '浏览', value: note.view_count || 0, icon: <EyeOutlined /> },
        { label: '评论页数', value: note.total_replay_page || 0 },
      )
    } else if (platform === 'zhihu') {
      stats.push(
        { label: '点赞', value: note.voteup_count || 0, icon: <HeartOutlined /> },
        { label: '评论', value: note.comment_count || 0, icon: <MessageOutlined /> },
      )
    }

    return (
      <Row gutter={16}>
        {stats.map((stat, index) => (
          <Col span={6} key={index}>
            <Statistic
              title={stat.label}
              value={stat.value}
              prefix={stat.icon}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
        ))}
      </Row>
    )
  }

  const tabItems = [
    {
      key: 'info',
      label: '笔记详情',
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题区域 */}
          <Card>
            <Title level={4} style={{ marginBottom: 8 }}>
              {note.title || note.desc?.substring(0, 100)}
            </Title>
            <Space size="middle">
              <Text type="secondary">
                作者: <Text strong>{note.nickname || note.user_name}</Text>
              </Text>
              {platform === 'xhs' && note.type && (
                <Text type="secondary">
                  类型: <Text strong>{note.type === 'video' ? '视频' : '图文'}</Text>
                </Text>
              )}
              {platform === 'zhihu' && note.content_type && (
                <Text type="secondary">
                  类型: <Text strong>{note.content_type}</Text>
                </Text>
              )}
            </Space>
          </Card>

          {/* 数据统计卡片 */}
          <Card title="数据统计">
            {renderStatistics()}
          </Card>

          {/* 内容详情 */}
          <Card title="内容详情">
            <Paragraph
              style={{
                maxHeight: 400,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                marginBottom: 16
              }}
            >
              {note.desc || note.content || '无内容描述'}
            </Paragraph>
            <Divider />
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text type="secondary">笔记ID: {note.note_id}</Text>
              <Text type="secondary">作者ID: {note.user_id}</Text>
              <Text type="secondary">
                发布时间: {note.time ? formatDateTime(note.time) : '-'}
              </Text>
              {note.last_update_time && (
                <Text type="secondary">
                  更新时间: {formatDateTime(note.last_update_time)}
                </Text>
              )}
            </Space>
          </Card>
        </Space>
      ),
    },
    {
      key: 'comments',
      label: `评论列表 (${commentsData?.total || 0})`,
      children: commentsLoading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin />
        </div>
      ) : (
        <>
          <List
            dataSource={commentsData?.items || []}
            locale={{ emptyText: <Empty description="暂无评论" /> }}
            renderItem={(item: Comment) => (
              <Card
                style={{ marginBottom: 12 }}
                size="small"
                styles={{ body: { padding: 12 } }}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar src={item.avatar} style={{ backgroundColor: '#87d068' }}>
                      {(item.nickname || item.user_name || 'U').charAt(0)}
                    </Avatar>
                  }
                  title={
                    <Space>
                      <span style={{ fontWeight: 500 }}>
                        {item.nickname || item.user_name}
                      </span>
                      <span style={{ fontSize: 12, color: '#999' }}>
                        {item.create_time ? formatDateTime(item.create_time) : '-'}
                      </span>
                    </Space>
                  }
                  description={
                    <div>
                      <div style={{ marginBottom: 8, color: '#333', whiteSpace: 'pre-wrap' }}>
                        {item.content}
                      </div>
                      <Space size="large">
                        <span style={{ fontSize: 12, color: '#666' }}>
                          <LikeOutlined style={{ marginRight: 4 }} />
                          {item.like_count || 0}
                        </span>
                        {(item.sub_comment_count ?? 0) > 0 && (
                          <span style={{ fontSize: 12, color: '#666' }}>
                            <MessageOutlined style={{ marginRight: 4 }} />
                            {item.sub_comment_count} 条回复
                          </span>
                        )}
                        {item.ip_location && (
                          <span style={{ fontSize: 12, color: '#999' }}>
                            {item.ip_location}
                          </span>
                        )}
                      </Space>
                    </div>
                  }
                />
              </Card>
            )}
          />
          {commentsData && commentsData.total > 0 && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Space>
                <span>共 {commentsData.total} 条评论</span>
                {commentPage > 1 && (
                  <a onClick={() => setCommentPage(commentPage - 1)}>上一页</a>
                )}
                <span>第 {commentPage} / {Math.ceil(commentsData.total / commentPageSize)} 页</span>
                {commentPage < Math.ceil(commentsData.total / commentPageSize) && (
                  <a onClick={() => setCommentPage(commentPage + 1)}>下一页</a>
                )}
              </Space>
            </div>
          )}
        </>
      ),
    },
  ]

  return (
    <Drawer
      title="笔记详情"
      placement="right"
      width={1000}
      onClose={onClose}
      open={visible}
      destroyOnClose
    >
      <Tabs items={tabItems} defaultActiveKey="info" />
    </Drawer>
  )
}

export default NoteDetailDrawer
