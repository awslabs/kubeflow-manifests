package base

import (
	"github.com/kubeflow/manifests/tests"
	"testing"
)

func TestKustomize(t *testing.T) {
	testCase := &tests.KustomizeTestCase{
		Package: "../../../../../../awsconfigs/common/istio-ingress/base",
		Expected: "test_data/expected",
	}

	tests.RunTestCase(t, testCase)
}