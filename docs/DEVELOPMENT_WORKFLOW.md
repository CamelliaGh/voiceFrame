# Development Workflow

## Standard Process for Each Task

### 1. Pre-Task Phase
- [ ] **Read and understand the PRD** (`docs/audio_poster_prd.md`)
- [ ] **Identify relevant PRD sections** for the current task
- [ ] **Ensure task aligns with PRD requirements**
- [ ] **Check if PRD needs updates** before starting work

### 2. Development Phase
- [ ] **Implement the feature/fix** according to PRD specifications
- [ ] **Follow existing code patterns** and architecture
- [ ] **Ensure Docker compatibility** (since we use containerized development)

### 3. Post-Task Phase
- [ ] **Run comprehensive tests** using `python run_tests.py`
- [ ] **Fix any test failures** before proceeding
- [ ] **Update PRD if needed** based on implementation discoveries
- [ ] **Document any deviations** from original PRD requirements

## Testing Strategy

### Automated Testing
- **Run after each task**: `python run_tests.py`
- **Run specific tests**: `python run_tests.py test_file_name.py`
- **All tests must pass** before considering task complete

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **File Migration Tests**: Storage and cleanup testing
- **Session Tests**: User session management
- **QR Code Tests**: Audio access and expiration

## PRD Update Guidelines

### When to Update PRD
- **New requirements discovered** during implementation
- **Technical constraints** that affect user experience
- **Performance optimizations** that change specifications
- **Security considerations** that impact features
- **User feedback** that changes priorities

### PRD Update Process
1. **Identify the section** that needs updating
2. **Document the change** with clear reasoning
3. **Update version/date** if significant changes
4. **Ensure consistency** across all related sections
5. **Review impact** on other features/requirements

## Quality Gates

### Before Starting Any Task
- [ ] PRD section reviewed and understood
- [ ] Task scope clearly defined
- [ ] Dependencies identified

### Before Marking Task Complete
- [ ] All tests passing
- [ ] Code follows project patterns
- [ ] PRD updated if needed
- [ ] Documentation updated
- [ ] No breaking changes introduced

## Current PRD Status

**Last Updated**: Based on current implementation
**Key Sections**:
- Core Features & Requirements (Section 3)
- Technical Architecture (Section 5)
- File Storage Policy (Section 3.5)
- User Experience Flow (Section 6)

## Test Coverage Areas

Based on current test files:
- ✅ File migration and cleanup
- ✅ Session management
- ✅ QR code generation and expiration
- ✅ Integration workflows
- ✅ Basic functionality

## Notes

- **Docker-first development**: All work should be compatible with containerized environment
- **Anonymous user model**: No user accounts, session-based approach
- **Pay-per-download**: Focus on preview → purchase conversion
- **File lifecycle**: Temporary → permanent storage migration
