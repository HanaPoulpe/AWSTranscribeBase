"""Create a lambda dependency layer"""
import os
import shutil
import subprocess

import aws_cdk.aws_lambda as aws_lambda


def include_requirements(path,
                         lambda_name,
                         *,
                         readers=None,
                         source_hash=None,
                         exclude=None,
                         follow=None,
                         ignore_mode=None,
                         follow_symlinks=None,
                         asset_hash=None,
                         asset_hash_type=None,
                         bundling=None) -> aws_lambda.Code:
    """
    Pack a lambda function with it requirements
    """
    requirements_file = os.path.join(path, "requirements.txt")
    output_dir = os.path.join(".build_lambda", lambda_name)

    # Install requirements for layer in the output_dir
    if not os.environ.get("SKIP_PIP"):
        # Note: Pip will create the output dir if it does not exist
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.copytree(path, output_dir)
        subprocess.check_call(
            f"pip install -r {requirements_file} -t {output_dir}"
        )

    return aws_lambda.Code.from_asset(
        output_dir,
        readers=readers,
        source_hash=source_hash,
        exclude=exclude,
        follow=follow,
        ignore_mode=ignore_mode,
        follow_symlinks=follow_symlinks,
        asset_hash=asset_hash,
        asset_hash_type=asset_hash_type,
        bundling=bundling,
    )
