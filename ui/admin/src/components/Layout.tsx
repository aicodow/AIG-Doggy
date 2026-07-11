import React from 'react';
import { Layout as ArcoLayout, Menu } from '@arco-design/web-react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  IconDashboard, IconSettings, IconFile, IconApps, IconUser,
} from '@arco-design/web-react/icon';

const { Sider, Content, Header } = ArcoLayout;

const menuItems = [
  { key: '/dashboard', icon: <IconDashboard />, label: '仪表盘' },
  { key: '/policies', icon: <IconSettings />, label: '策略管理' },
  { key: '/audit', icon: <IconFile />, label: '审计日志' },
  { key: '/apps', icon: <IconApps />, label: '应用管理' },
  { key: '/users', icon: <IconUser />, label: '用户管理' },
];

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <ArcoLayout style={{ minHeight: '100vh' }}>
      <Sider width={220} collapsible breakpoint="lg">
        <div style={{ padding: 16, textAlign: 'center', fontWeight: 700, fontSize: 18, color: '#fff' }}>
          AIG-Doggy
        </div>
        <Menu
          selectedKeys={[location.pathname]}
          onClickMenuItem={(key) => navigate(key)}
          items={menuItems}
          style={{ marginTop: 8 }}
        />
      </Sider>
      <ArcoLayout>
        <Header style={{ padding: '0 24px', background: '#fff', borderBottom: '1px solid #e5e6eb' }}>
          <h2 style={{ margin: 0, lineHeight: '56px' }}>
            {menuItems.find((m) => m.key === location.pathname)?.label || '仪表盘'}
          </h2>
        </Header>
        <Content style={{ padding: 24, background: '#f7f8fa' }}>{children}</Content>
      </ArcoLayout>
    </ArcoLayout>
  );
};

export default AppLayout;