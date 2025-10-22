# ClinChat-RAG Clinical Dashboard

## Overview

React-based clinical dashboard for the ClinChat-RAG system, providing an intuitive interface for healthcare professionals to interact with AI-powered clinical decision support tools.

## Features

### 🏥 Clinical Workflow Integration
- **Patient Context Management**: Maintain patient context across sessions
- **Document Analysis Interface**: Upload and analyze clinical documents
- **AI Analysis Results**: View and interpret AI-powered insights
- **Role-Based Access Control**: Different interfaces for different healthcare roles

### 📊 Analytics & Reporting
- **Real-time Analytics**: Monitor system usage and performance
- **Compliance Reports**: HIPAA, GxP, and FDA compliance tracking
- **Audit Trail Visualization**: Complete audit log interface
- **Performance Metrics**: AI provider performance comparisons

### 🔒 Security & Compliance
- **Authentication**: Multi-factor authentication support
- **Session Management**: Secure session handling with auto-refresh
- **PHI Protection**: Automated PHI detection and handling
- **Audit Logging**: Comprehensive user action tracking

### 📱 Responsive Design
- **Mobile-First**: Optimized for tablets and mobile devices
- **Offline Capabilities**: Core functionality available offline
- **Progressive Web App**: Installable on devices

## Technology Stack

- **Frontend**: React 18+ with TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **State Management**: React Query + Context API
- **Routing**: React Router v6
- **Forms**: Formik + Yup validation
- **Charts**: Recharts
- **PDF Processing**: React-PDF
- **HTTP Client**: Axios

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- ClinChat-RAG backend API running on port 8002

### Installation

```bash
# Navigate to dashboard directory
cd ui/clinical-dashboard

# Install dependencies
npm install

# Start development server
npm start
```

The dashboard will be available at `http://localhost:3000`

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Serve production build (requires serve package)
npx serve -s build
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── common/          # Generic components
│   ├── forms/           # Form components
│   ├── charts/          # Data visualization
│   └── layout/          # Layout components
├── pages/               # Page components
│   ├── auth/            # Authentication pages
│   ├── dashboard/       # Main dashboard
│   ├── documents/       # Document management
│   ├── patient/         # Patient views
│   ├── analysis/        # Analysis results
│   ├── compliance/      # Compliance reports
│   └── admin/           # Administration
├── contexts/            # React contexts
├── hooks/               # Custom React hooks
├── services/            # API services
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── theme/               # MUI theme configuration
```

## Key Components

### Authentication System
- JWT token-based authentication
- Role-based access control (RBAC)
- Session management with auto-refresh
- Secure cookie storage

### Document Processing Interface
- Drag-and-drop file upload
- Multi-format support (PDF, DOCX, TXT, etc.)
- Real-time processing status
- PHI detection alerts

### AI Analysis Dashboard
- Fusion AI provider selection
- Real-time analysis progress
- Interactive results visualization
- Confidence scoring display

### Compliance Monitoring
- Live compliance status dashboard
- Automated alert system
- Audit log viewer with filtering
- Report generation tools

## Configuration

### Environment Variables

Create a `.env` file in the dashboard root:

```bash
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8002
REACT_APP_API_PREFIX=/api/v1

# Feature Flags
REACT_APP_ENABLE_OFFLINE_MODE=true
REACT_APP_ENABLE_PWA=true
REACT_APP_ENABLE_ANALYTICS=true

# Security
REACT_APP_SESSION_TIMEOUT=1800000  # 30 minutes
REACT_APP_ENABLE_MFA=false

# UI Configuration
REACT_APP_THEME_MODE=light
REACT_APP_DEFAULT_LANGUAGE=en
```

## API Integration

The dashboard integrates with the ClinChat-RAG backend API:

### Authentication Endpoints
- `POST /auth/login` - User authentication
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Token refresh
- `GET /auth/profile` - User profile

### Document Processing
- `POST /documents/upload` - Upload documents
- `GET /documents/{id}` - Get document details
- `POST /documents/{id}/analyze` - Trigger AI analysis

### AI Analysis
- `POST /fusion/analyze` - Fusion AI analysis
- `GET /analysis/{id}` - Get analysis results
- `GET /fusion/capabilities` - Available AI providers

### Compliance & Audit
- `GET /compliance/status` - Compliance status
- `GET /audit/logs` - Audit log entries
- `POST /compliance/reports` - Generate reports

## User Roles & Permissions

### Clinical Roles
- **Physician**: Full clinical access, patient management
- **Nurse**: Patient care access, limited administrative
- **Pharmacist**: Medication-focused analysis access
- **Medical Assistant**: Basic document processing

### Administrative Roles
- **Admin**: Full system access and configuration
- **Compliance Officer**: Compliance monitoring and reporting
- **IT Support**: System monitoring and user management

### Permission System
```typescript
const permissions = {
  // Document permissions
  'documents.upload': ['physician', 'nurse', 'medical_assistant'],
  'documents.analyze': ['physician', 'nurse', 'pharmacist'],
  'documents.delete': ['physician', 'admin'],
  
  // Patient permissions
  'patients.view': ['physician', 'nurse'],
  'patients.edit': ['physician'],
  
  // Administrative permissions
  'users.manage': ['admin'],
  'compliance.view': ['admin', 'compliance_officer'],
  'system.configure': ['admin'],
};
```

## Security Features

### Data Protection
- All PHI data encrypted in transit and at rest
- Automatic PHI detection and masking
- Secure file upload with virus scanning
- Data retention policy enforcement

### Access Control
- Multi-factor authentication support
- Role-based access control (RBAC)
- Session timeout management
- IP address restrictions (configurable)

### Audit & Compliance
- Complete user action logging
- HIPAA-compliant audit trails
- Automated compliance reporting
- Data breach detection alerts

## Development Guidelines

### Code Style
- TypeScript for type safety
- ESLint + Prettier for code formatting
- Husky for pre-commit hooks
- Conventional commits for git messages

### Component Development
- Functional components with hooks
- Custom hooks for business logic
- Material-UI components for consistency
- Responsive design principles

### Testing Strategy
- Jest for unit testing
- React Testing Library for component testing
- Cypress for end-to-end testing
- Coverage reports required

### Performance Optimization
- Code splitting with React.lazy
- Memoization for expensive operations
- Virtualization for large lists
- Service worker for offline capabilities

## Deployment

### Production Build
```bash
# Build optimized bundle
npm run build

# Build includes:
# - Minified JavaScript/CSS
# - Source maps
# - Service worker
# - Progressive Web App manifest
```

### Docker Deployment
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment-Specific Configuration
- Development: Hot reloading, debug tools enabled
- Staging: Production build with debug info
- Production: Optimized build, analytics enabled

## Troubleshooting

### Common Issues

**Authentication Issues**
- Check API endpoint configuration
- Verify CORS settings on backend
- Clear browser cookies/localStorage

**File Upload Problems**
- Check file size limits
- Verify supported file formats
- Check network connectivity

**Performance Issues**
- Clear browser cache
- Check for console errors
- Monitor network requests

### Debug Tools
- React Developer Tools browser extension
- Redux DevTools (if using Redux)
- Network tab for API debugging
- Console logs for error tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following code guidelines
4. Add tests for new functionality
5. Submit a pull request

## License

This project is part of the ClinChat-RAG system and follows the same licensing terms.

## Support

For technical support or questions:
- Check the documentation in `/docs`
- Review existing GitHub issues
- Contact the development team

---

**Note**: This dashboard is designed specifically for healthcare environments and includes HIPAA-compliant features. Ensure proper configuration and testing before production deployment.