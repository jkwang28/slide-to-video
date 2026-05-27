import os


from .project import Project, ProjectConfig
from .narration import create_narration_script


def slide_to_video(
    *,
    project_config: ProjectConfig,
):
    # Create the output directory if it does not exist
    output_dir = project_config["output_dir"]
    if os.path.exists(output_dir):
        project_file = f"{output_dir}/project.yaml"
        if not os.path.exists(project_file):
            # remove the directory
            os.system(f"rm -rf {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    prepare_narration_script(project_config)
    if project_config.get("draft_only"):
        print(f"Editable narration script is ready: {project_config['script']}")
        return

    if "script_dict" in project_config:
        replace_dict = {}
        script_dict = project_config["script_dict"]
        with open(script_dict, "r") as f:
            lines = f.readlines()
            for line in lines:
                original_text, new_text = line.strip().split(":")
                replace_dict[original_text.strip()] = new_text.strip()
        project_config["script_dict"] = replace_dict

    project = Project(
        name="project",
        config=project_config,
    )
    project.build()
    project.save()


def prepare_narration_script(project_config: ProjectConfig):
    needs_draft = project_config.get("draft_only") or project_config.get("draft_script")
    if not needs_draft:
        return

    draft_script = project_config.get("draft_script")
    if not draft_script:
        draft_script = f"{project_config['output_dir']}/script.txt"
        project_config["draft_script"] = draft_script

    if project_config.get("script") and not project_config.get("regenerate_draft"):
        return

    script_path = create_narration_script(
        slide_path=project_config["slide"],
        output_path=draft_script,
        language=project_config.get("language", "zh-cn"),
        provider=project_config.get("script_provider", "template"),
        overwrite=project_config.get("regenerate_draft", False),
        config=project_config.as_dict()
        if hasattr(project_config, "as_dict")
        else dict(project_config),
    )
    project_config["script"] = script_path
