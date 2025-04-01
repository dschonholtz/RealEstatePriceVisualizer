# Claude Code Guidelines for RealEstatePriceVisualizer

## Project Overview
RealEstatePriceVisualizer is a web application that uses publicly available Massachusetts real estate data to track and visualize current property prices and their rates of change over time. The tool aims to provide an intuitive interface for users to explore real estate trends across different neighborhoods.

## Development Workflow
1. **Issue Creation**: All work should be tracked through well-scoped GitHub issues, organized into epics as needed.
2. **Branching**: Create a new branch for each issue using a descriptive name (e.g., `add-feature-x`, `fix-bug-y`).
3. **Development**: Write production-quality code following our style guidelines.
4. **Testing**: Implement comprehensive tests (unit, integration, frontend) before submitting code.
5. **Pull Requests**: Create PRs with clear descriptions linking to the related issue.
6. **Code Review**: Address all review comments promptly.
7. **Merge**: Once approved and tests pass, merge the PR to the main branch.

## Code Style Guidelines
- Use consistent indentation (2 spaces) and formatting
- Follow the DRY (Don't Repeat Yourself) principle
- Keep functions small and focused on a single responsibility
- Use descriptive variable and function names
- Add comments for complex logic but prioritize self-documenting code
- Document public APIs and interfaces

## Testing Requirements
- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test interactions between components
- **Frontend Tests**: Test UI components and user flows
- **Test Coverage**: Aim for at least 80% test coverage for critical paths
- **Test-Driven Development**: Write tests before implementing features when possible

## Documentation Standards
- **README.md**: Maintain an up-to-date project overview and setup instructions
- **API Documentation**: Document all endpoints, parameters, and responses
- **Code Comments**: Add JSDoc or similar comments for functions and classes
- **Architecture Diagrams**: Keep diagrams updated when making significant changes
- **User Guides**: Provide clear instructions for end users

## Data Handling Guidelines
- Document all data sources with attribution
- Implement proper error handling for data loading and processing
- Use appropriate data structures for efficient querying and visualization
- Follow data privacy best practices
- Document the data schema and relationships

## Performance Considerations
- Optimize database queries for large datasets
- Implement pagination for large result sets
- Use appropriate caching strategies
- Optimize frontend rendering for smooth visualizations
- Monitor and address performance bottlenecks

## Accessibility Requirements
- Follow WCAG 2.1 AA standards
- Ensure keyboard navigation works properly
- Provide alternative text for images and visualizations
- Maintain sufficient color contrast
- Test with screen readers

## Security Guidelines
- Validate and sanitize all user inputs
- Implement proper authentication and authorization
- Use HTTPS for all communications
- Follow secure coding practices
- Regularly update dependencies to address security vulnerabilities

## Deployment Process
- Use CI/CD for automated testing and deployment
- Maintain staging and production environments
- Document environment configuration requirements
- Implement feature flags for gradual rollouts
- Maintain a rollback strategy

This document serves as a guide for both human developers and Claude Code when working on the RealEstatePriceVisualizer project. All contributors should follow these guidelines to maintain consistency and quality across the codebase.