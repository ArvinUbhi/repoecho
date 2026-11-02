# Java repository learning

First find the actual build layout. Do not assume Maven, Gradle, a particular Java version, Spring, or a single module.

| Question | Inspect | Typical note |
|---|---|---|
| Build and target JDK | Parent/module `pom.xml`; Gradle build/settings; toolchains; wrapper properties; CI | `build-and-test` |
| Module boundaries | Parent modules/settings includes; source/test trees; public interfaces | `module-NAME` |
| Runtime entry points | `main`, framework annotations, service loaders, deployment config | `entrypoints` |
| Dependency contracts | Interfaces, implementations, registration/config, call sites | `api-NAME` |
| Threading and lifecycle | Executors, ownership, synchronization, shutdown, daemon/process launch | `concurrency-contract` |
| Tests | Actual test sources, fixtures, test plugins/tasks, CI commands | `test-NAME` |

For Maven, capture both parent and relevant child POMs; a child POM alone may hide inherited compiler flags, profiles, dependency versions, or test setup. For Gradle, include relevant settings, version catalogs and convention plugins. Do not execute Gradle/Maven merely to build the cache: builds can run repository code and resolve dependencies. Run them only as part of the authorized engineering task and report actual results.

For Java 8 applications, distinguish source/target/release settings from the JDK used to run the build. A source file using `java.time` is not proof of the complete compatibility contract. Inspect CI/build evidence before claiming Java 8 support. The helper's Python runtime is independent of the app's JDK and adds no Java dependency.

Examples of useful scopes:

- `**/pom.xml` catches changed and newly added Maven modules.
- `**/build.gradle*` plus `**/settings.gradle*` catches Gradle build-layout changes.
- `service/src/main/java/com/example/process/**` watches a package tree.
- `**/src/test/**` is broad; prefer the relevant module or package when possible.
- `**/META-INF/services/**` catches service-loader registrations.

`**` matches zero or more path segments. Quote globs so the shell does not expand them. Include resources/configuration affecting behavior; source-only summaries miss dependency injection and runtime switches. Scope membership covers only eligible, non-excluded files. Git submodules are separate roots; learn them explicitly when needed.

For other languages use the same method: discover manifests, entry points, module boundaries, public contracts, tests and configuration from evidence. Filename heuristics in `plan` are only navigation hints, not a parser or dependency graph.
