package aws

import (
	"github.com/kubeflow/manifests/tests"
	"testing"
)

func TestKustomize(t *testing.T) {
	testCase := &tests.KustomizeTestCase{
		Package: "../../../../../../apps/pipeline/upstream/env/aws",
		Expected: "test_data/expected",
	}

	tests.RunTestCase(t, testCase)
}