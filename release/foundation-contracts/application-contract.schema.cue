package applicationcontract

import (
	"list"
	"strings"
	"struct"
)

// ApplicationContract v1alpha8 and v1alpha9 are release-owned product meaning.
// v1alpha8 retains its published runtime-values/v1alpha1 semantics. v1alpha9
// deliberately introduces runtime-values/v1alpha2 so setup-derived standard Pod
// labels can cross the fixed chart boundary without an App-local values source.
// Neither version selects what a customer runs. setup.yaml remains the only
// customer desired-state authority and the canonical resolver binds setup
// selections to the exact versioned contract.

#Name:             string & =~"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"
#Reference:        string & =~"^[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]$" & !~"//" & !~"(^|/)\\.\\.?(/|$)"
#DotPath:          string & =~"^[A-Za-z0-9][A-Za-z0-9_-]*(\\.[A-Za-z0-9][A-Za-z0-9_-]*)*$"
#NonEmpty:         string & =~".*[^[:space:]].*" & !~"REPLACE|TODO|CHANGEME"
#APIGroup:         "" | #NonEmpty
#SemVer:           string & =~"^[0-9]+\\.[0-9]+\\.[0-9]+([+-][0-9A-Za-z.-]+)?$"
#Digest:           string & =~"^sha256:[0-9a-f]{64}$"
#OciRepository:    string & =~"^[A-Za-z0-9.-]+(:[0-9]{1,5})?/[A-Za-z0-9._/-]+$" & !~"@|:latest$"
#Port:             int & >=1 & <=65535
#PositiveDuration: string & =~"^[1-9][0-9]*(ms|s|m|h)$"
#ConfigPath:       string & =~"^[a-z][a-zA-Z0-9]*(\\.[a-z][a-zA-Z0-9]*)*$" & !~"(?i)(^|\\.)[a-z0-9]*(password|passwd|secret|token|credential|privatekey|apikey)(\\.|$)"
#ApplicationClass: "adask-vendor" | "third-party-vendor" | "customer" | "platform-test"
#HTTPPath:         string & =~"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]*$" & !~"//" & !~"(^|/)\\.\\.?(/|$)"

// Capability abilities are stable application-facing contracts, not provider
// or implementation IDs. Requiring a lowercase multi-segment namespace closes
// accidental single-product values such as "longhorn" while leaving the
// Catalog-owned ability vocabulary independently extensible.
#CapabilityAbility: string & =~"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(/[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"

// Intervals are deliberately closed and normalized. Ordering and intersection
// are evaluated once by the canonical resolver; consumers may not reinterpret
// these strings or silently widen an interval.
#VersionInterval: {
	minInclusive: #SemVer
	maxExclusive: #SemVer
}

#Condition: {
	kind: "always"
} | {
	kind:  "configuration-equals"
	field: #ConfigPath
	value: null | bool | number | string
}

#Artifact: {
	role:       "chart" | "image" | "manifest-bundle" | "migration"
	repository: #OciRepository
	digest:     #Digest
	mediaType:  #NonEmpty
	if role == "migration" {
		mediaType: "application/vnd.oci.image.manifest.v1+json"
	}
}

#BooleanConfigurationField: {
	type:             "boolean"
	customerRequired: bool
	default?:         bool
	render: helmValuePath: #DotPath
	if customerRequired {
		default?: _|_
	}
}

#IntegerConfigurationField: {
	type:             "integer"
	customerRequired: bool
	default?:         int
	minimum?:         int
	maximum?:         int
	render: helmValuePath: #DotPath
	if customerRequired {
		default?: _|_
	}
	if minimum != _|_ && maximum != _|_ {
		maximum: >=minimum
	}
	if default != _|_ && minimum != _|_ {
		default: >=minimum
	}
	if default != _|_ && maximum != _|_ {
		default: <=maximum
	}
}

#NumberConfigurationField: {
	type:             "number"
	customerRequired: bool
	default?:         number
	minimum?:         number
	maximum?:         number
	render: helmValuePath: #DotPath
	if customerRequired {
		default?: _|_
	}
	if minimum != _|_ && maximum != _|_ {
		maximum: >=minimum
	}
	if default != _|_ && minimum != _|_ {
		default: >=minimum
	}
	if default != _|_ && maximum != _|_ {
		default: <=maximum
	}
}

#StringConfigurationField: {
	type:             "string"
	customerRequired: bool
	default?:         string
	pattern?:         string
	minLength?:       int & >=0
	maxLength?:       int & >=0
	render: helmValuePath: #DotPath
	if customerRequired {
		default?: _|_
	}
	if minLength != _|_ && maxLength != _|_ {
		maxLength: >=minLength
	}
}

#EnumConfigurationField: {
	type:             "enum"
	customerRequired: bool
	values: list.MinItems(1) & list.UniqueItems & [...#NonEmpty]
	default?: #NonEmpty
	render: helmValuePath: #DotPath
	if customerRequired {
		default?: _|_
	}
	if default != _|_ {
		_defaultAllowed: list.Contains(values, default) & true
	}
}

#ConfigurationField: #BooleanConfigurationField |
	#IntegerConfigurationField |
	#NumberConfigurationField |
	#StringConfigurationField |
	#EnumConfigurationField

#RequirementBase: {
	condition: #Condition
}

#FoundationAPIRequirement: {
	#RequirementBase
	kind: "foundation-api"
	api: {
		id:      #Reference
		version: #VersionInterval
		features: *[] | (list.UniqueItems & [...#Name])
	}
}

#CapabilityRequirement: {
	#RequirementBase
	kind: "capability"
	binding: {
		// This names the stable ability/API contract. setup.yaml and the
		// Capability Catalog select and admit its concrete implementation.
		ability:    #CapabilityAbility
		apiVersion: #VersionInterval
		features: *[] | (list.UniqueItems & [...#Name])
		cardinality: "one"
		sharing:     "shared" | "dedicated"
	}
}

#ServiceAPIRequirement: {
	#RequirementBase
	kind: "service-api"
	binding: {
		serviceContract: #Reference
		apiVersion:      #VersionInterval
		protocol:        "https" | "grpc-tls" | "s3-tls" | "postgresql-tls" | "events-tls"
		features: *[] | (list.UniqueItems & [...#Name])
		cardinality:    "one"
		authentication: "none" | "secret-reference" | "workload-identity"
	}
}

#KubernetesDeployAPIRequirement: {
	#RequirementBase
	kind: "kubernetes-deploy-api"
	resources: list.MinItems(1) & list.UniqueItems & [...{
		group:   #APIGroup
		version: #NonEmpty
		kind:    #NonEmpty
	}]
}

#KubernetesRuntimeAPIRequirement: {
	#RequirementBase
	kind: "kubernetes-runtime-api"
	access: list.MinItems(1) & list.UniqueItems & [...{
		group:    #APIGroup
		resource: #NonEmpty
		verbs: list.MinItems(1) & list.UniqueItems & [...("get" | "list" | "watch" | "create" | "update" | "patch" | "delete")]
		scope: "namespace"
	}]
}

#InfrastructureRequirement: {
	#RequirementBase
	kind:    "foundation-infrastructure"
	ability: "compute" | "scheduling" | "runtime-class" | "ephemeral-storage"
	qualities: struct.MinFields(1) & {[#Name]: #NonEmpty}
}

#Requirement: #FoundationAPIRequirement |
	#CapabilityRequirement |
	#ServiceAPIRequirement |
	#KubernetesDeployAPIRequirement |
	#KubernetesRuntimeAPIRequirement |
	#InfrastructureRequirement

#ProvidedAPI: {
	protocol:       "https" | "grpc-tls" | "events-tls"
	contract:       #Reference
	version:        #SemVer
	authentication: "none" | "oidc" | "mtls"
	visibility:     "namespace" | "cluster" | "ingress"
}

#SecretRequirement: {
	condition: #Condition
	required:  true
	// Secrets are least-privilege workload inputs. The renderer must never
	// guess whether an application-wide requirement belongs in one workload or
	// disclose it to every workload by default.
	workloadRefs: list.MinItems(1) & list.UniqueItems & [...#Name]
	delivery: {
		kind: "environment"
		name: string & =~"^[A-Z_][A-Z0-9_]*$"
	} | {
		kind:      "file"
		mountPath: string & =~"^/[^[:space:]]+$" & !~"//" & !~"/$" & !~"/\\.\\.?(/|$)"
		fileName:  #Name
	}
}

#IngressInterface: {
	protocol:       "https"
	port:           #Port
	tls:            "required"
	authentication: "none" | "oidc" | "mtls"
	exposure: list.MinItems(1) & list.UniqueItems & [...("internal" | "public")]
}

#EgressPurpose: {
	condition: #Condition
	protocol:  "https" | "grpc-tls" | "s3-tls" | "postgresql-tls" | "events-tls"
	ports: list.MinItems(1) & list.UniqueItems & [...#Port]
	destination:    "setup-binding"
	authentication: "none" | "secret-reference" | "workload-identity"
}

#ResourceQuantity: string & =~"^[1-9][0-9]*(m|Ki|Mi|Gi|Ti)?$"
#ResourceProfile: {
	requests: {
		cpu:    #ResourceQuantity
		memory: #ResourceQuantity
	}
	limits: {
		cpu:    #ResourceQuantity
		memory: #ResourceQuantity
	}
}

#AlertRule: {
	signal:    "availability" | "error-rate" | "dependency" | "queue-backlog" | "database-connectivity" | "custom-metric"
	severity:  "warning" | "critical"
	metric:    #NonEmpty
	operator:  ">" | ">=" | "<" | "<=" | "=="
	threshold: number
	for:       #PositiveDuration
}

#ApplicationSecurityProfile: {
	profile:                  "restricted-v1"
	podSecurity:              "restricted"
	runAsNonRoot:             true
	privileged:               false
	allowPrivilegeEscalation: false
	hostNamespaces: {
		network: false
		pid:     false
		ipc:     false
	}
	hostPathVolumes: false
	seccompProfile:  "RuntimeDefault"
	linuxCapabilities: {
		add: []
		drop: ["ALL"]
	}
	serviceAccounts: {
		scope:          "per-workload"
		rbacScope:      "namespace"
		tokenAutomount: "runtime-api-requirement-only"
	}
	// v1alpha3 exposes no normal-application exception path. APP-030 owns
	// any future explicit, reviewed and versioned exception contract.
	exceptions: []
}

#HealthEndpoint: {
	workloadRef:    #Name
	protocol:       "http"
	method:         "GET"
	path:           #HTTPPath
	port:           #Port
	successStatus:  200
	authentication: "none"
}

#HealthProbeTiming: {
	initialDelaySeconds: int & >=0 & <=600
	periodSeconds:       int & >=1 & <=300
	timeoutSeconds:      int & >=1 & <=periodSeconds
	failureThreshold:    int & >=1 & <=20
	successThreshold:    int & >=1 & <=10
}

#ApplicationHealthContract: {
	liveness: {
		#HealthEndpoint
		semantics: "process-health"
		timing: {
			#HealthProbeTiming
			successThreshold: 1
		}
	}
	readiness: {
		#HealthEndpoint
		semantics: "accepting-traffic"
		timing:    #HealthProbeTiming
		// Only active refs are expected at runtime. The central resolver
		// evaluates their conditions and records that exact subset once.
		dependencyRequirementRefs: list.UniqueItems & [...#Name]
	}
	version: {
		#HealthEndpoint
		semantics:      "exact-release-identity"
		timeoutSeconds: int & >=1 & <=30
		responseSchema: "platform.adask-b.io/application-version-response/v1alpha1"
	}
	_endpointIdentities: [
		{workloadRef: liveness.workloadRef, protocol: liveness.protocol, path: liveness.path, port: liveness.port},
		{workloadRef: readiness.workloadRef, protocol: readiness.protocol, path: readiness.path, port: readiness.port},
		{workloadRef: version.workloadRef, protocol: version.protocol, path: version.path, port: version.port},
	] & list.UniqueItems
}

#WorkloadUnit: {
	kind: "deployment" | "statefulset" | "job" | "cronjob"
	imageArtifactRefs: list.MinItems(1) & list.UniqueItems & [...#Name]
	// A workload receives a Kubernetes API token only when at least one of
	// these release-declared, namespace-scoped requirements is active after
	// setup configuration is resolved. Empty means automount=false.
	runtimeAPIRequirementRefs: *[] | (list.UniqueItems & [...#Name])
	if kind == "job" {
		completion: {
			timeout:      #PositiveDuration
			backoffLimit: int & >=0
		}
	}
	if kind == "cronjob" {
		completion: {
			timeout:      #PositiveDuration
			backoffLimit: int & >=0
		}
		scheduleContract: "setup-selected"
	}
}

// A rollback target is declared by the release being reversed. That release
// can know the exact older release and the data transition it introduced;
// the older target cannot safely predict arbitrary future releases. The
// package and contract digests prevent a semantic version from authorizing
// different bytes.
#RollbackTargetRelease: {
	version:        #SemVer
	packageDigest:  #Digest
	contractDigest: #Digest
}

#RollbackDataSafety: {
	mode: "stateless"
} | {
	mode: "backward-compatible"
} | {
	mode: "database-rollback-required"
} | {
	mode: "data-restore-required"
	restore: {
		point:       "pre-upgrade"
		consistency: "crash-consistent" | "application-consistent"
	}
} | {
	mode:        "migration-reversal-required"
	artifactRef: #Name
}

#RollbackTarget: {
	release:    #RollbackTargetRelease
	dataSafety: #RollbackDataSafety
}

#ApplicationRollback: ({
	applicationState: "stateless"
	policy:           "supported"
	targets: list.MinItems(1) & list.UniqueItems & [...(#RollbackTarget & {
		dataSafety: mode: "stateless"
	})]
} | {
	applicationState: "stateful"
	policy:           "supported"
	targets: list.MinItems(1) & list.UniqueItems & [...(#RollbackTarget & {
		dataSafety: mode: "backward-compatible" | "database-rollback-required" | "data-restore-required" | "migration-reversal-required"
	})]
} | {
	applicationState: "stateless"
	policy:           "forward-fix-only"
	reason:           "release-unsupported"
} | {
	applicationState: "stateful"
	policy:           "forward-fix-only"
	reason:           "release-unsupported" | "data-incompatible" | "migration-irreversible"
})

// Workload removal is always a GitOps-prune operation. Customer data, backup
// and external-resource destruction are deliberately outside that operation.
// A release that declares retained data must bind any eventual destruction to
// a separate, exact, approval-gated lifecycle contract; setup and an approved
// Plan remain authoritative for whether that operation is ever requested.
#RemovalDestructionContract: {
	id!:      #Reference
	version!: #SemVer
	digest!:  #Digest
}

#ApplicationRemoval: {
	workload!: action!: "prune-generated-gitops"
	data!: ({
		onWorkloadRemoval!: "not-applicable"
		destruction!: mode!: "not-applicable"
		retentionReview!: "not-applicable"
	} | {
		onWorkloadRemoval!: "retain"
		destruction!: {
			mode!:     "separate-approved-operation"
			approval!: "required"
			contract!: #RemovalDestructionContract
		}
		retentionReview!: "required"
	})
	backups!: onWorkloadRemoval!: "not-applicable" | "retain-until-customer-policy-expiry"
	externalResources!: onWorkloadRemoval!: "not-applicable" | "retain"
}

// The target release owns every supported data migration into itself. Source
// identity is exact so a version label cannot authorize different bytes. The
// Platform owns the fixed phase order; the release declares only the
// application-specific artifact and the safety conditions that coordination
// must satisfy.
#MigrationSourceRelease: {
	version:        #SemVer
	packageDigest:  #Digest
	contractDigest: #Digest
}

#MigrationMaintenance: {
	mode:      "online"
	readiness: "keep-serving"
} | {
	mode:      "quiesce"
	readiness: "withdraw-traffic"
}

#ApplicationMigrationTransition: {
	sourceRelease: #MigrationSourceRelease
	artifactRef:   #Name
	checkpoint: {
		mode:        "required"
		kind:        "pre-migration-recovery-point"
		consistency: "crash-consistent" | "application-consistent"
	}
	maintenance: #MigrationMaintenance
	execution: {
		interface:    "platform.adask-b.io/application-migration-job/v1alpha1"
		replayPolicy: "same-plan-resumable"
	}
}

#ApplicationMigration: {
	mode: "none"
} | {
	mode:        "application-owned"
	transitions: list.MinItems(1) & list.UniqueItems & [...#ApplicationMigrationTransition]
}

#ApplicationContract: {
	apiVersion: "platform.adask-b.io/application-contract/v1alpha8" | "platform.adask-b.io/application-contract/v1alpha9"
	kind:       "ApplicationContract"
	metadata: {
		// Stable across releases. Version, chart, image, namespace and Helm
		// release names are deliberately not application identity.
		name: #Name
	}

	release: {
		version:           #SemVer
		evidencePolicyRef: #Reference
		// The package repository is release-owned, but its manifest digest cannot
		// be embedded in the package that it identifies. setup.yaml or the
		// read-only admission input binds that external exact digest instead.
		delivery: {
			repository: #OciRepository
			mediaType:  "application/vnd.zarf.package.v1"
		}
		publisher: {
			applicationClass: #ApplicationClass
			artifactClass:    "vendor-app" | "customer-app"
			policyRef:        #Reference
		}
		artifacts: struct.MinFields(2) & {[#Name]: #Artifact}
		_artifactDigests: [for _, artifact in artifacts {artifact.digest}] & list.UniqueItems
		_deploymentArtifacts: [for _, artifact in artifacts if artifact.role == "chart" || artifact.role == "manifest-bundle" {artifact}] & list.MinItems(1) & list.MaxItems(1)
		_runtimeImages: [for _, artifact in artifacts if artifact.role == "image" {artifact}] & list.MinItems(1)
		if publisher.applicationClass == "customer" {
			publisher: artifactClass: "customer-app"
		}
		if publisher.applicationClass != "customer" {
			publisher: artifactClass: "vendor-app"
		}
	}

	compatibility: {
		profiles: list.MinItems(1) & list.UniqueItems & [..."onprem-linux-vm-v1"]
		architectures: list.MinItems(1) & list.UniqueItems & [..."amd64"]
		foundationAPI: {
			id:      #Reference
			version: #VersionInterval
		}
	}

	configuration: {
		fields: {[#ConfigPath]: #ConfigurationField}
		_paths: [for fieldName, _ in fields {fieldName}]
		_prefixConflicts: [
			for left in _paths
			for right in _paths
			if left != right && strings.HasPrefix(right, "\(left).") {right},
		] & list.MaxItems(0)
		_valuePaths: [for _, field in fields {field.render.helmValuePath}] & list.UniqueItems
	}

	requirements: {[#Name]: #Requirement}
	provides: {
		apis: *{} | {[#Name]: #ProvidedAPI}
	}

	deployment: {
		mode:        "helm"
		artifactRef: #Name
		// Every compliant chart consumes the generated runtime contract at this
		// fixed root. Making the interface explicit prevents a chart from silently
		// ignoring security, probe or Secret wiring while accepting ordinary values.
		renderer!: {
			apiVersion!:    "platform.adask-b.io/application-runtime-values/v1alpha1" | "platform.adask-b.io/application-runtime-values/v1alpha2"
			helmValuePath!: "platformRuntime"
		}
		replicasValuePath:  #DotPath
		resourcesValuePath: #DotPath
		imageMappings: struct.MinFields(1) & {[#Name]: {
			repositoryValuePath: #DotPath
			digestValuePath:     #DotPath
		}}
		_allValuePaths: [
			renderer.helmValuePath,
			replicasValuePath,
			resourcesValuePath,
			for _, field in configuration.fields {field.render.helmValuePath},
			for _, mapping in imageMappings {mapping.repositoryValuePath},
			for _, mapping in imageMappings {mapping.digestValuePath},
		] & list.UniqueItems
		_valuePathPrefixConflicts: [
			for left in _allValuePaths
			for right in _allValuePaths
			if left != right && strings.HasPrefix(right, "\(left).") {right},
		] & list.MaxItems(0)
	}
	// Published v1alpha8 meaning is immutable. v1alpha9 is the first contract
	// whose fixed chart interface carries centrally resolved standard Pod labels.
	// This validation expression checks the pair without supplying either
	// required release-owned field when the document omits it.
	_versionPairValid: ((apiVersion == "platform.adask-b.io/application-contract/v1alpha8" && deployment.renderer.apiVersion == "platform.adask-b.io/application-runtime-values/v1alpha1") || (apiVersion == "platform.adask-b.io/application-contract/v1alpha9" && deployment.renderer.apiVersion == "platform.adask-b.io/application-runtime-values/v1alpha2")) & true
	release: artifacts: (deployment.artifactRef): role: "chart"
	for artifactId, artifact in release.artifacts if artifact.role == "image" {
		deployment: imageMappings: (artifactId): _
	}
	for artifactId, _ in deployment.imageMappings {
		release: artifacts: (artifactId): role: "image"
	}

	workloads: struct.MinFields(1) & {[#Name]: #WorkloadUnit}
	for _, workload in workloads {
		for imageRef in workload.imageArtifactRefs {
			release: artifacts: (imageRef): role: "image"
		}
		for requirementRef in workload.runtimeAPIRequirementRefs {
			requirements: (requirementRef): kind: "kubernetes-runtime-api"
		}
	}
	for _, requirement in secrets {
		for workloadRef in requirement.workloadRefs {
			workloads: (workloadRef): _
		}
	}
	_runtimeAPIAssignments: {
		for requirementName, requirement in requirements if requirement.kind == "kubernetes-runtime-api" {
			(requirementName): list.MinItems(1) & [
				for workloadName, workload in workloads
				if list.Contains(workload.runtimeAPIRequirementRefs, requirementName) {
					workloadName
				},
			]
		}
	}
	for _, requirement in requirements if requirement.condition.kind == "configuration-equals" {
		configuration: fields: (requirement.condition.field): _
	}

	secrets: *{} | {[#Name]: #SecretRequirement}
	_environmentSecretTargets: [for _, requirement in secrets if requirement.delivery.kind == "environment" {requirement.delivery.name}] & list.UniqueItems
	_fileSecretTargets: [for _, requirement in secrets if requirement.delivery.kind == "file" {{mountPath: requirement.delivery.mountPath, fileName: requirement.delivery.fileName}}] & list.UniqueItems
	for _, requirement in secrets if requirement.condition.kind == "configuration-equals" {
		configuration: fields: (requirement.condition.field): _
	}
	network: {
		ingress: *{} | {[#Name]: #IngressInterface}
		egress: *{} | {[#Name]: #EgressPurpose}
		defaultDeny: true
	}
	// Every supported external purpose is also an exact service-API
	// requirement. Keeping one stable ID and one condition/protocol/auth meaning
	// prevents an egress declaration from becoming an untyped Internet escape.
	for purposeName, purpose in network.egress {
		requirements: (purposeName): {
			kind:      "service-api"
			condition: purpose.condition
			binding: {
				protocol:       purpose.protocol
				authentication: purpose.authentication
			}
		}
	}
	for requirementName, requirement in requirements if requirement.kind == "service-api" {
		network: egress: (requirementName): {
			condition:      requirement.condition
			protocol:       requirement.binding.protocol
			authentication: requirement.binding.authentication
		}
	}
	for _, requirement in network.egress if requirement.condition.kind == "configuration-equals" {
		configuration: fields: (requirement.condition.field): _
	}
	resources: {
		replicas: {
			minimum: int & >=1
			maximum: int & >=minimum
		}
		profiles: struct.MinFields(1) & {[#Name]: #ResourceProfile}
	}
	security: #ApplicationSecurityProfile
	privacy: {
		personalData: bool
		dataCategories: *[] | (list.UniqueItems & [...#Name])
		externalProcessing: bool
		deletion:           "not-applicable" | "supported" | "product-process-required"
		export:             "not-applicable" | "supported" | "product-process-required"
	}
	data: {
		persistent: bool
		backup: {
			required:    bool
			consistency: "not-applicable" | "crash-consistent" | "application-consistent"
		}
		if !persistent {
			backup: {
				required:    false
				consistency: "not-applicable"
			}
		}
		if backup.required {
			backup: consistency: "crash-consistent" | "application-consistent"
		}
	}
	if data.persistent {
		lifecycle: rollback: applicationState: "stateful"
		lifecycle: removal: data: onWorkloadRemoval: "retain"
	}
	if !data.persistent {
		lifecycle: removal: data: onWorkloadRemoval: "not-applicable"
	}
	if data.backup.required {
		lifecycle: removal: {
			data: onWorkloadRemoval: "retain"
			backups: onWorkloadRemoval: "retain-until-customer-policy-expiry"
		}
	}
	if !data.backup.required {
		lifecycle: removal: backups: onWorkloadRemoval: "not-applicable"
	}
	health: #ApplicationHealthContract
	for endpoint in [health.liveness, health.readiness, health.version] {
		workloads: (endpoint.workloadRef): kind: "deployment" | "statefulset"
	}
	for requirementRef in health.readiness.dependencyRequirementRefs {
		requirements: (requirementRef): kind: "foundation-api" | "capability" | "service-api" | "kubernetes-runtime-api" | "foundation-infrastructure"
	}
	observability: {
		metrics: {
			required: bool
			path?:    string & =~"^/"
			if required {path: string & =~"^/"}
		}
		structuredLogs: true
		tracing:        "not-supported" | "optional" | "required"
		alerts: {
			rules: *[] | (list.UniqueItems & [...#AlertRule])
		}
	}
	let _backupConsistency = data.backup.consistency
	lifecycle: {
		upgrade:  "rolling" | "recreate" | "coordinated-migration"
		rollback: #ApplicationRollback
		repair:   "gitops"
		removal!: #ApplicationRemoval
		migration: #ApplicationMigration
	}
	if lifecycle.migration.mode == "none" {
		lifecycle: upgrade: "rolling" | "recreate"
	}
	if lifecycle.migration.mode == "application-owned" {
		lifecycle: upgrade: "coordinated-migration"
		data: {
			persistent: true
			backup: required: true
		}
		_migrationCheckpointConsistency: [
			for transition in lifecycle.migration.transitions {
				transition.checkpoint.consistency
			},
		] & [..._backupConsistency]
		for transition in lifecycle.migration.transitions {
			release: artifacts: (transition.artifactRef): role: "migration"
		}
	}
	if lifecycle.rollback.policy == "supported" {
		for target in lifecycle.rollback.targets if target.dataSafety.mode == "migration-reversal-required" {
			release: artifacts: (target.dataSafety.artifactRef): role: "migration"
		}
	}
}
