import React from 'react';
import { Card, Grid, Statistic, Skeleton } from '@arco-design/web-react';
import { IconArrowUp, IconArrowDown } from '@arco-design/web-react/icon';
import { useQuery } from '@tanstack/react-query';

const { Row, Col } = Grid;

const fetchStats = async () => {
  const res = await fetch('/v1/admin/health/services');
  return res.json();
};

const fetchPlugins = async () => {
  const res = await fetch('/v1/admin/plugins');
  return res.json();
};

const Dashboard: React.FC = () => {
  const { data: health, isLoading: healthLoading } = useQuery({ queryKey: ['health'], queryFn: fetchStats });
  const { data: plugins, isLoading: pluginsLoading } = useQuery({ queryKey: ['plugins'], queryFn: fetchPlugins });

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Skeleton loading={healthLoading} text={{ rows: 2 }}>
              <Statistic title="网关状态" value={health?.gateway === 'healthy' ? '正常' : '异常'} />
            </Skeleton>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Skeleton loading={healthLoading} text={{ rows: 2 }}>
              <Statistic title="NIM 内容安全" value={health?.nim_content_safety === 'healthy' ? '正常' : '异常'} />
            </Skeleton>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Skeleton loading={healthLoading} text={{ rows: 2 }}>
              <Statistic title="Kafka" value={health?.kafka === 'healthy' ? '正常' : '异常'} />
            </Skeleton>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Skeleton loading={pluginsLoading} text={{ rows: 2 }}>
              <Statistic title="已注册护栏插件" value={plugins?.plugins?.length || 0} suffix="个" />
            </Skeleton>
          </Card>
        </Col>
      </Row>

      <Card title="护栏插件列表">
        <ul>
          {plugins?.plugins?.map((p: any) => (
            <li key={p.plugin_id}>
              {p.plugin_id} — {p.plugin_name} ({p.stage}) [{p.maturity}]
            </li>
          )) || <li>加载中...</li>}
        </ul>
      </Card>
    </div>
  );
};

export default Dashboard;