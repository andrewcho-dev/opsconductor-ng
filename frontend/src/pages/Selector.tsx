/**
 * Selector Page
 * Page wrapper for the Selector Search component
 */

import React from 'react';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import SelectorSearch from '../components/SelectorSearch';

const SelectorPage: React.FC = () => {
  return (
    <PageContainer>
      <PageHeader title="Tool Selector" />
      <SelectorSearch />
    </PageContainer>
  );
};

export default SelectorPage;