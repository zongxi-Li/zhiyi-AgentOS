import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import GenericArtifactPanel from './GenericArtifactPanel.vue'


const artifact = {
  artifactId: 'artifact_1',
  type: 'report',
  title: '智能装配生产线实施方案',
  mediaType: 'text/markdown',
  content: '推荐采用模块化柔性装配线。',
  structuredData: {
    title: '智能装配生产线实施方案',
    executiveSummary: '方案满足预算、周期和产能约束。',
    sections: [
      { title: '产能分析', content: '目标节拍需优化至 50 秒。', sourceFields: ['capacity_plan'] },
      { title: '实施计划', content: '项目在 26 周内完成。', sourceFields: ['solution_design'] }
    ],
    calculations: [{
      name: '有效产能', formula: '理论产能 × OEE', result: '244,800 台/年',
      inputs: ['288,000 台', '85%'], assumptions: ['节拍 50 秒']
    }],
    assumptions: ['成本为估算值'],
    openQuestions: ['确认设备供应商报价'],
    sourceRefs: ['src_task_input']
  }
}

describe('GenericArtifactPanel', () => {
  it('presents structured final delivery before audit step outputs', async () => {
    const wrapper = mount(GenericArtifactPanel, {
      props: {
        status: 'completed',
        finalReport: '推荐采用模块化柔性装配线。',
        finalArtifacts: [artifact],
        stepOutputs: [
          { stepId: 'analysis', name: '通用分析', status: 'completed', output: { findings: ['a'] } },
          { stepId: 'deliver', name: '成果生成', status: 'completed', output: { final_answer: 'done' } }
        ]
      }
    })

    expect(wrapper.text()).toContain('最终交付说明')
    expect(wrapper.text()).toContain('智能装配生产线实施方案')
    expect(wrapper.text()).toContain('方案满足预算、周期和产能约束')
    expect(wrapper.findAll('.solution-section')).toHaveLength(2)
    expect(wrapper.find('.delivery-facts').text()).toContain('2方案章节')
    expect(wrapper.find('.step-output-section').text()).toContain('过程产出')
    expect(wrapper.findAll('details')).toHaveLength(2)

    await wrapper.findAll('.delivery-tabs button')[1].trigger('click')
    expect(wrapper.find('.calculation-card').text()).toContain('244,800 台/年')

    await wrapper.findAll('.delivery-tabs button')[2].trigger('click')
    expect(wrapper.find('.decision-grid').text()).toContain('确认设备供应商报价')
  })

  it('renders an unstructured final report as safe Markdown', () => {
    const wrapper = mount(GenericArtifactPanel, {
      props: {
        status: 'completed',
        finalReport: [
          '# Final delivery',
          '',
          '**Complete result.**',
          '',
          '| Risk | Level |',
          '| --- | --- |',
          '| Acceptance | High |',
          '',
          '<script>alert("unsafe")</script>'
        ].join('\n'),
        finalArtifacts: [],
        stepOutputs: []
      }
    })

    const report = wrapper.find('.report-fallback')
    expect(report.find('h1').text()).toBe('Final delivery')
    expect(report.find('strong').text()).toBe('Complete result.')
    expect(report.find('table').text()).toContain('AcceptanceHigh')
    expect(report.find('script').exists()).toBe(false)
    expect(report.html()).toContain('&lt;script&gt;')
    expect(wrapper.text()).toContain('已生成')
  })

  it('shows a synchronization state instead of zero final artifacts after completion', () => {
    const wrapper = mount(GenericArtifactPanel, {
      props: {
        status: 'completed',
        finalReport: null,
        finalArtifacts: [],
        stepOutputs: [{ stepId: 'analysis', name: '分析', status: 'completed', output: { result: 'done' } }]
      }
    })

    expect(wrapper.text()).toContain('正在整理最终成果')
    expect(wrapper.text()).not.toContain('最终交付物 0 项')
  })

  it('turns degraded JSON fields into readable requirement and acceptance lists', () => {
    const structuredArtifact = {
      ...artifact,
      structuredData: {
        ...artifact.structuredData,
        sections: [
          {
            title: '任务理解与需求',
            content: [
              '- **native_general_agent.constraints**: [{"constraint":"首期覆盖30家重点门店","mandatory":true,"source":"试点目标"}]',
              '- **native_general_agent.task_summary**: 为连锁企业设计应急补货方案。'
            ].join('\n'),
            sourceFields: ['constraints', 'task_summary']
          },
          {
            title: '任务理解与需求 2',
            content: '- **native_general_agent_2.acceptance_criteria**: [{"criterion":"核心民生商品缺货率不超过8%","metric":"缺货率","requirement_id":"REQ-002","target":"≤8%"}]',
            sourceFields: ['acceptance_criteria']
          },
          {
            title: '任务理解与需求 3',
            content: '- **native_general_agent_2.requirements**: [{"id":"REQ-001","priority":"高","requirement":"建立面向极端天气的应急补货机制","source":"试点目标"}]',
            sourceFields: ['requirements']
          },
          {
            title: '流程与资源',
            content: '- **native_general_agent_3.process_steps**: [{"activities":["提取业务背景"],"id":"step1","name":"任务理解","owner":"项目经理"},{"activities":["形成需求清单"],"id":"step2","nam…',
            sourceFields: ['process_steps']
          }
        ]
      }
    }
    const wrapper = mount(GenericArtifactPanel, {
      props: {
        status: 'completed',
        finalReport: null,
        finalArtifacts: [structuredArtifact],
        stepOutputs: [{
          stepId: 'native_general_agent_3',
          name: '流程拆解',
          status: 'completed',
          output: {
            process_steps: [
              { activities: ['提取业务背景'], id: 'step1', name: '任务理解', owner: '项目经理', quality_gate: '约束完整' },
              { activities: ['形成需求清单'], id: 'step2', name: '需求分析', owner: '业务分析师', quality_gate: '覆盖所有目标' }
            ]
          }
        }]
      }
    })

    expect(wrapper.findAll('.structured-field')).toHaveLength(5)
    expect(wrapper.findAll('.record-list')).toHaveLength(4)
    expect(wrapper.text()).toContain('约束条件')
    expect(wrapper.text()).toContain('验收标准')
    expect(wrapper.text()).toContain('目标值≤8%')
    expect(wrapper.text()).toContain('需求清单')
    expect(wrapper.text()).toContain('优先级高')
    expect(wrapper.text()).toContain('流程步骤')
    expect(wrapper.text()).toContain('需求分析')
    expect(wrapper.text()).toContain('质量门槛覆盖所有目标')
    expect(wrapper.text()).not.toContain('[{"constraint"')
    expect(wrapper.text()).not.toContain('"nam…')
  })
})
