# OpsConductor Design System

## Overview

This document describes the standardized design system for OpsConductor. All pages and components should follow these guidelines to ensure a consistent look and feel across the entire application.

## Design Philosophy

- **Consistency**: All pages use the same layout structure, colors, typography, and spacing
- **Simplicity**: Clean, professional design with minimal visual clutter
- **Efficiency**: Dense layouts that maximize information density without sacrificing usability
- **Accessibility**: Clear visual hierarchy and readable typography

## Core Files

### CSS Files

1. **`/frontend/src/styles/global.css`** - **SINGLE SOURCE OF TRUTH**
   - Contains all standardized design tokens, layout patterns, and component styles
   - This is the primary CSS file that defines the entire design system
   - All new pages should use classes from this file

2. **`/frontend/src/styles/standardized.css`** - Legacy file (being phased out)
   - Contains older design system styles
   - Kept for backward compatibility
   - Will be gradually removed as components are migrated

3. **`/frontend/src/index.css`** - Entry point
   - Imports global.css and standardized.css
   - Contains minimal legacy compatibility styles

### React Components

Located in `/frontend/src/components/`:

1. **`PageContainer.tsx`** - Wrapper for all pages
2. **`PageHeader.tsx`** - Standardized page header with title and actions
3. **`StatusBadge.tsx`** - Status indicators with automatic color mapping
4. **`StatPill.tsx`** - Clickable stat pills for navigation

## Design Tokens

### Colors

#### Primary Colors
```css
--primary-blue: #2563eb
--primary-blue-hover: #1d4ed8
--primary-blue-light: #dbeafe
--primary-blue-dark: #1d4ed8
```

#### Status Colors
```css
--success-green: #059669
--success-green-dark: #047857
--success-green-light: #d1fae5

--warning-orange: #d97706
--warning-orange-light: #fef3c7

--danger-red: #dc2626
--danger-red-light: #fee2e2
```

#### Neutral Colors
```css
--neutral-50: #f8fafc   /* Backgrounds */
--neutral-100: #f1f5f9  /* Subtle backgrounds */
--neutral-200: #e2e8f0  /* Borders */
--neutral-300: #cbd5e1  /* Input borders */
--neutral-500: #64748b  /* Muted text */
--neutral-700: #334155  /* Body text */
--neutral-800: #1e293b  /* Headings */
```

### Typography

```css
--font-size-xs: 0.75rem    /* 12px - Labels, badges */
--font-size-sm: 0.875rem   /* 14px - Body text */
--font-size-base: 1rem     /* 16px - Default */
--font-size-lg: 1.125rem   /* 18px - Section headers */
--font-size-xl: 1.25rem    /* 20px - Page titles */
```

### Spacing

```css
--space-1: 0.25rem  /* 4px */
--space-2: 0.5rem   /* 8px */
--space-3: 0.75rem  /* 12px */
--space-4: 1rem     /* 16px */
--space-6: 1.5rem   /* 24px */
--space-8: 2rem     /* 32px */
```

## Page Layout Structure

### Standard Page Template

```tsx
import React from 'react';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import StatPill from '../components/StatPill';
import { Target, MessageSquare } from 'lucide-react';

const MyPage: React.FC = () => {
  return (
    <PageContainer>
      <PageHeader title="Page Title">
        <StatPill icon={Target} label="Assets" count={10} to="/assets" />
        <StatPill icon={MessageSquare} label="AI Assistant" to="/ai-chat" />
      </PageHeader>

      {/* Page content goes here */}
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <div className="section-header">Section Title</div>
          <div className="section-content">
            {/* Content */}
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default MyPage;
```

### Layout Classes

#### Page Container
```tsx
<PageContainer>
  {/* All page content */}
</PageContainer>
```
- Provides consistent padding: `8px 12px`
- Sets max-width and font-size
- Full viewport height with flex layout

#### Page Header
```tsx
<PageHeader title="My Page">
  {/* Action buttons, stat pills, etc. */}
</PageHeader>
```
- Displays page title on the left
- Actions/badges on the right
- Consistent spacing and alignment

#### Dashboard Grid
```tsx
<div className="dashboard-grid">
  <div className="dashboard-section">...</div>
  <div className="dashboard-section">...</div>
</div>
```
- 2-column layout by default: `minmax(400px, 1fr) minmax(600px, 2fr)`
- 3-column variant: Add `three-column` class
- Responsive: Collapses to single column on smaller screens

#### Dashboard Section
```tsx
<div className="dashboard-section">
  <div className="section-header">Title</div>
  <div className="section-content">
    {/* Content */}
  </div>
</div>
```
- White background with border
- Rounded corners
- Flex column layout
- Section header with gray background

## Components

### Buttons

#### Primary Button
```tsx
<button className="btn btn-primary">Save</button>
```

#### Secondary Button
```tsx
<button className="btn btn-secondary">Cancel</button>
```

#### Danger Button
```tsx
<button className="btn btn-danger">Delete</button>
```

#### Icon Button
```tsx
<button className="btn-icon" title="Add">
  <Plus size={18} />
</button>
```

#### Icon Button Variants
```tsx
<button className="btn-icon btn-danger">
  <Trash2 size={18} />
</button>

<button className="btn-icon btn-ghost">
  <X size={18} />
</button>
```

### Badges

#### Status Badge
```tsx
import StatusBadge from '../components/StatusBadge';

<StatusBadge status="active" />
<StatusBadge status="failed" />
<StatusBadge status="running" />
<StatusBadge variant="success">Custom Text</StatusBadge>
```

Status types automatically map to colors:
- `active`, `succeeded`, `online` → Green
- `inactive`, `failed`, `offline` → Red
- `running`, `pending` → Blue
- `queued`, `maintenance` → Orange
- `decommissioned` → Gray

#### Stat Pill
```tsx
import StatPill from '../components/StatPill';
import { Target } from 'lucide-react';

<StatPill icon={Target} label="Assets" count={25} to="/assets" />
```

### Cards

#### Standard Card
```tsx
<div className="card">
  <div className="card-header">
    <h3 className="card-title">Card Title</h3>
  </div>
  <div className="card-body">
    Card content
  </div>
</div>
```

#### Subcard (within sections)
```tsx
<div className="subcard">
  <div className="subcard-header">Subcard Title</div>
  <div>Subcard content</div>
</div>
```

### Tables

```tsx
<table className="table">
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data 1</td>
      <td>Data 2</td>
    </tr>
  </tbody>
</table>
```

### Forms

```tsx
<div className="form-group">
  <label className="form-label">Field Label</label>
  <input type="text" className="form-control" />
</div>

<div className="form-group">
  <label className="form-label">Select Field</label>
  <select className="form-control">
    <option>Option 1</option>
  </select>
</div>

<div className="form-group">
  <label className="form-label">Textarea</label>
  <textarea className="form-control"></textarea>
</div>
```

### Detail Views

```tsx
<div className="detail-group">
  <div className="detail-label">Field Name</div>
  <div className="detail-value">Field Value</div>
</div>
```

### Dropdowns

```tsx
<div className="dropdown">
  <button className="btn-icon">
    <MoreVertical size={18} />
  </button>
  <div className="dropdown-menu">
    <button className="dropdown-item">Action 1</button>
    <button className="dropdown-item">Action 2</button>
  </div>
</div>
```

### Empty States

```tsx
<div className="empty-state">
  <h3>No Data</h3>
  <p>There are no items to display.</p>
</div>
```

### Loading States

```tsx
<div className="loading-state">
  <p>Loading...</p>
</div>

{/* Full page loading */}
<div className="loading-overlay">
  <div className="loading-spinner"></div>
</div>
```

## Standard Header Badges

All pages should include these standard badges in the header:

1. **Assets Count** - Links to `/assets`
   ```tsx
   <StatPill icon={Target} label="Assets" count={assetCount} to="/assets" />
   ```

2. **AI Assistant** - Links to `/ai-chat`
   ```tsx
   <StatPill icon={MessageSquare} label="AI Assistant" to="/ai-chat" />
   ```

**Removed Badges:**
- ❌ Jobs badge (removed)
- ❌ Runs badge (removed)

## Utility Classes

### Text Utilities
```css
.text-center      /* Center align text */
.text-right       /* Right align text */
.text-muted       /* Muted gray text */
.text-danger      /* Red text */
.text-success     /* Green text */
.text-warning     /* Orange text */
.font-mono        /* Monospace font */
.truncate         /* Truncate with ellipsis */
```

### Layout Utilities
```css
.flex             /* Display flex */
.flex-col         /* Flex column */
.items-center     /* Align items center */
.justify-between  /* Justify space between */
.gap-2            /* Gap 8px */
.gap-4            /* Gap 16px */
```

### Spacing Utilities
```css
.mt-2, .mt-4      /* Margin top */
.mb-2, .mb-4      /* Margin bottom */
.p-4              /* Padding all sides */
```

## Best Practices

### DO ✅

1. **Use PageContainer and PageHeader** for all pages
2. **Use design tokens** (CSS variables) instead of hardcoded colors
3. **Use standardized components** (StatusBadge, StatPill, etc.)
4. **Follow the dashboard-grid layout** for multi-column pages
5. **Use consistent spacing** with CSS variables
6. **Include standard header badges** (Assets, AI Assistant)
7. **Use semantic HTML** and proper heading hierarchy
8. **Test responsive behavior** on different screen sizes

### DON'T ❌

1. **Don't use inline styles** unless absolutely necessary
2. **Don't hardcode colors** - use CSS variables
3. **Don't create custom layouts** - use dashboard-grid
4. **Don't add Jobs or Runs badges** to headers (removed)
5. **Don't use Bootstrap classes** - use our design system
6. **Don't create duplicate styles** - reuse existing classes
7. **Don't skip PageContainer** - all pages need it
8. **Don't use inconsistent spacing** - use CSS variables

## Migration Guide

### Converting Existing Pages

1. **Wrap page in PageContainer**
   ```tsx
   import PageContainer from '../components/PageContainer';
   
   return (
     <PageContainer>
       {/* existing content */}
     </PageContainer>
   );
   ```

2. **Replace header with PageHeader**
   ```tsx
   import PageHeader from '../components/PageHeader';
   
   <PageHeader title="Page Title">
     {/* badges and actions */}
   </PageHeader>
   ```

3. **Update badges**
   - Remove Jobs and Runs badges
   - Keep Assets and AI Assistant badges
   - Use StatPill component

4. **Replace custom styles**
   - Remove inline `<style>` tags where possible
   - Use classes from global.css
   - Only keep page-specific styles if truly unique

5. **Update layout structure**
   - Use `dashboard-grid` for multi-column layouts
   - Use `dashboard-section` for content sections
   - Use `section-header` and `section-content`

## Examples

### Assets Page (Reference Implementation)

The Assets page (`/frontend/src/pages/Assets.tsx`) is the reference implementation for the design system. It demonstrates:

- Proper use of PageContainer (via dense-dashboard class)
- Standard header with badges
- Dashboard grid layout (2 columns)
- Section headers and content areas
- Icon buttons and dropdowns
- Consistent spacing and colors

### Dashboard Page

The Dashboard page demonstrates:
- Service health monitoring
- AI monitoring
- Full-width sections
- Responsive layout

### AI Chat Page

The AI Chat page demonstrates:
- Sidebar layout
- Chat interface
- Session management
- Consistent header

## Future Enhancements

- [ ] Dark mode support
- [ ] Additional color themes
- [ ] More reusable components
- [ ] Animation utilities
- [ ] Accessibility improvements
- [ ] Component documentation with Storybook

## Questions?

For questions about the design system, refer to:
- This document (DESIGN_SYSTEM.md)
- `/frontend/src/styles/global.css` (source of truth)
- Assets page implementation (reference example)