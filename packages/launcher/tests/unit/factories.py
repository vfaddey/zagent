from zagent_launcher.application.dto import LauncherRunSpec

DUMMY_IMAGE = "dummy-image:test"

def create_launcher_run_spec(**kwargs) -> LauncherRunSpec:
    spec_kwargs = dict(
        run_id="run-1",
        runtime_image=DUMMY_IMAGE,
        runtime_workdir="/workspace",
        model_api_key_env="OPENAI_API_KEY",
        policy_network="restricted",
        runtime_env=(),
    )
    spec_kwargs.update(kwargs)
    return LauncherRunSpec(**spec_kwargs)

def create_run_yaml(
    image: str = DUMMY_IMAGE,
    network: str = "restricted",
    run_id: str = "default",
    api_key_env: str = "OPENAI_API_KEY",
) -> str:
    return f"""\
run_id: {run_id}
model:
  api_key_env: {api_key_env}
runtime:
  image: {image}
  workdir: /workspace
  env: {{}}
policy:
  network: {network}
"""
