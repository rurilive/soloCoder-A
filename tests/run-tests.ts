import type { TestResult, TestReport } from './helpers/test-utils';
import { runAuthTests } from './auth.test';
import { runMediaTests } from './media.test';
import { runAdminTests } from './admin.test';
import { runTelegramTests } from './telegram.test';

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms.toFixed(2)}ms`;
  }
  return `${(ms / 1000).toFixed(2)}s`;
}

function getEmoji(passed: boolean): string {
  return passed ? '✅' : '❌';
}

function generateMarkdownReport(report: TestReport): string {
  const totalTests = report.totalTests;
  const passedTests = report.passedTests;
  const failedTests = report.failedTests;
  const passRate = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : '0';

  let markdown = `# 测试报告

> 生成时间: ${report.completedAt}
> 总耗时: ${formatDuration(report.duration)}

---

## 测试概览

| 指标 | 数值 |
|------|------|
| **总测试数** | ${totalTests} |
| **通过** | ${passedTests} ✅ |
| **失败** | ${failedTests} ❌ |
| **通过率** | ${passRate}% |
| **开始时间** | ${report.startedAt} |
| **结束时间** | ${report.completedAt} |
| **总耗时** | ${formatDuration(report.duration)} |

---

## 分类统计

| 测试分类 | 总数 | 通过 | 失败 | 通过率 |
|---------|------|------|------|--------|
`;

  for (const [category, stats] of Object.entries(report.categories)) {
    const rate = stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(1) : '0';
    markdown += `| ${category} | ${stats.total} | ${stats.passed} | ${stats.failed} | ${rate}% |\n`;
  }

  markdown += `
---

## 详细结果

`;

  const categories = Object.keys(report.categories);
  for (const category of categories) {
    const categoryResults = report.results.filter(r => r.category === category);
    const categoryStats = report.categories[category];
    const categoryPassRate = categoryStats.total > 0 
      ? ((categoryStats.passed / categoryStats.total) * 100).toFixed(1) 
      : '0';

    markdown += `### ${category} (${categoryStats.passed}/${categoryStats.total} - ${categoryPassRate}%)

`;

    const passedResults = categoryResults.filter(r => r.passed);
    const failedResults = categoryResults.filter(r => !r.passed);

    if (failedResults.length > 0) {
      markdown += `#### ❌ 失败的测试

`;
      for (const result of failedResults) {
        markdown += `**${getEmoji(result.passed)} ${result.name}**
- 耗时: ${formatDuration(result.duration)}
- 错误: \`${result.error}\`

`;
      }
    }

    if (passedResults.length > 0) {
      markdown += `#### ✅ 通过的测试

`;
      const passedList = passedResults
        .map(r => `${getEmoji(r.passed)} ${r.name} (${formatDuration(r.duration)})`)
        .join('\n- ');
      markdown += `- ${passedList}\n\n`;
    }
  }

  const failedResults = report.results.filter(r => !r.passed);
  if (failedResults.length > 0) {
    markdown += `---

## 失败详情

`;

    for (const result of failedResults) {
      markdown += `### ${result.category} / ${result.name}

\`\`\`
${result.error}
\`\`\`

`;
    }
  }

  markdown += `---

## Mock 数据说明

测试使用了预定义的 Mock 数据:

### 测试用户

| 用户名 | 邮箱 | 密码 | 角色 |
|--------|------|------|------|
| admin | admin@imgbed.local | admin123 | 管理员 |
| demo_user | demo@imgbed.local | demo123 | 普通用户 |
| test_user_01 | test01@imgbed.local | test123 | 普通用户 |

### 测试覆盖范围

- **认证模块**: 密码哈希、用户管理、会话管理
- **媒体模块**: 文件CRUD、访问控制、过期管理、R2存储
- **管理模块**: 用户状态切换、文件管理、系统清理
- **Telegram模块**: Bot用户管理、文件上传、Webhook验证

---

*测试报告结束*
`;

  return markdown;
}

function generateConsoleReport(report: TestReport): string {
  const totalTests = report.totalTests;
  const passedTests = report.passedTests;
  const failedTests = report.failedTests;
  const passRate = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : '0';

  let output = '\n';
  output += '='.repeat(60) + '\n';
  output += '                    测试报告\n';
  output += '='.repeat(60) + '\n\n';
  
  output += `总测试数: ${totalTests}\n`;
  output += `通过: ${passedTests} ✅\n`;
  output += `失败: ${failedTests} ❌\n`;
  output += `通过率: ${passRate}%\n`;
  output += `总耗时: ${formatDuration(report.duration)}\n\n`;
  
  output += '-'.repeat(60) + '\n';
  output += '分类统计\n';
  output += '-'.repeat(60) + '\n\n';

  for (const [category, stats] of Object.entries(report.categories)) {
    const rate = stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(1) : '0';
    const status = stats.failed === 0 ? '✅' : '❌';
    output += `${status} ${category}: ${stats.passed}/${stats.total} (${rate}%)\n`;
  }

  const failedResults = report.results.filter(r => !r.passed);
  if (failedResults.length > 0) {
    output += '\n' + '-'.repeat(60) + '\n';
    output += '失败详情\n';
    output += '-'.repeat(60) + '\n\n';

    for (const result of failedResults) {
      output += `❌ [${result.category}] ${result.name}\n`;
      output += `   错误: ${result.error}\n\n`;
    }
  }

  output += '\n' + '='.repeat(60) + '\n';
  
  if (failedTests === 0) {
    output += '🎉 所有测试通过!\n';
  } else {
    output += `⚠️ 有 ${failedTests} 个测试失败\n`;
  }
  
  output += '='.repeat(60) + '\n';

  return output;
}

export async function runAllTests(): Promise<TestReport> {
  const startedAt = new Date().toISOString();
  const startTime = performance.now();

  const allResults: TestResult[] = [];

  console.log('\n📋 开始运行测试...\n');

  console.log('🔐 运行认证模块测试...');
  const authResults = await runAuthTests();
  allResults.push(...authResults);
  console.log(`   完成: ${authResults.filter(r => r.passed).length}/${authResults.length}\n`);

  console.log('📁 运行媒体模块测试...');
  const mediaResults = await runMediaTests();
  allResults.push(...mediaResults);
  console.log(`   完成: ${mediaResults.filter(r => r.passed).length}/${mediaResults.length}\n`);

  console.log('👨‍💼 运行管理模块测试...');
  const adminResults = await runAdminTests();
  allResults.push(...adminResults);
  console.log(`   完成: ${adminResults.filter(r => r.passed).length}/${adminResults.length}\n`);

  console.log('🤖 运行Telegram模块测试...');
  const telegramResults = await runTelegramTests();
  allResults.push(...telegramResults);
  console.log(`   完成: ${telegramResults.filter(r => r.passed).length}/${telegramResults.length}\n`);

  const endTime = performance.now();
  const completedAt = new Date().toISOString();
  const duration = endTime - startTime;

  const totalTests = allResults.length;
  const passedTests = allResults.filter(r => r.passed).length;
  const failedTests = allResults.filter(r => !r.passed).length;

  const categories: Record<string, { total: number; passed: number; failed: number }> = {};
  for (const result of allResults) {
    if (!categories[result.category]) {
      categories[result.category] = { total: 0, passed: 0, failed: 0 };
    }
    categories[result.category].total++;
    if (result.passed) {
      categories[result.category].passed++;
    } else {
      categories[result.category].failed++;
    }
  }

  const report: TestReport = {
    totalTests,
    passedTests,
    failedTests,
    duration,
    startedAt,
    completedAt,
    results: allResults,
    categories,
  };

  return report;
}

async function main() {
  try {
    const report = await runAllTests();
    
    console.log(generateConsoleReport(report));
    
    const markdownReport = generateMarkdownReport(report);
    const fs = require('fs');
    const path = require('path');
    
    const reportPath = path.join(__dirname, '..', 'TEST_REPORT.md');
    fs.writeFileSync(reportPath, markdownReport, 'utf-8');
    
    console.log(`\n📄 详细报告已保存到: ${reportPath}`);
    
    process.exit(report.failedTests > 0 ? 1 : 0);
  } catch (error) {
    console.error('测试运行失败:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { generateMarkdownReport, generateConsoleReport };
