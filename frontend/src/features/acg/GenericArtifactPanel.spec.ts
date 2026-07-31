import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import GenericArtifactPanel from './GenericArtifactPanel.vue'


describe('GenericArtifactPanel', () => {
  it('shows one final result and keeps step outputs available', () => {
    const wrapper = mount(GenericArtifactPanel, {
      props: {
        finalReport: '# Final delivery\n\nComplete result.',
        finalArtifacts: [{
          artifactId: 'artifact_1',
          type: 'report',
          title: 'Final delivery',
          mediaType: 'text/markdown',
          content: '# Final delivery\n\nComplete result.',
          structuredData: {}
        }],
        stepOutputs: [
          { stepId: 'analysis', name: 'Analysis', status: 'completed', output: { findings: ['a'] } },
          { stepId: 'deliver', name: 'Delivery', status: 'completed', output: { final_answer: '# Final' } }
        ]
      }
    })

    expect(wrapper.text()).toContain('最终交付物')
    expect(wrapper.text()).toContain('步骤产出')
    expect(wrapper.text()).toContain('2 项')
    expect(wrapper.find('.final-report').text()).toContain('Complete result.')
    expect(wrapper.findAll('details')).toHaveLength(2)
  })
})
