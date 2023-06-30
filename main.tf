terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "app_server" {
  ami           = "ami-03190fe20ef6b1419"
  instance_type = "t4g.xlarge"
  key_name      = "satbox"

  root_block_device {
    delete_on_termination = true
    volume_type           = "gp3"
    volume_size           = 30
    tags = {
      App = "satbox"
    }
  }

  tags = {
    Name = "satbox"
    App  = "satbox"
  }
}
