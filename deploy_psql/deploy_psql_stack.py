from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class DeployPsqlStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. VPC with public and private subnets
        vpc = ec2.Vpc(self, "MyVpc06Jun2025",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="pubsub06Jun2025", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="pvtsub06Jun2025", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24
                ),
            ],
        )

        # 2. Security group for bastion host (allow SSH only from your IP)
        bastion_sg = ec2.SecurityGroup(self, "BastionSG06Jun2025", vpc=vpc, description="Bastion SG06Jun2025")
        bastion_sg.add_ingress_rule(
            ec2.Peer.ipv4("136.32.251.101/32"),  # <-- Replace with your public IP
            ec2.Port.tcp(22),
            "Allow SSH only from my laptop 136.32.251.101"
        )

        # 3. Security group for RDS (allow Postgres from bastion only)
        rds_sg = ec2.SecurityGroup(self, "RDSSG06Jun2025", vpc=vpc, description="RDSSG06Jun2025")
        rds_sg.add_ingress_rule(
            bastion_sg, ec2.Port.tcp(5432), "Allow Postgresql access from Bastion host only"
        )

        # 4. Bastion host in public subnet
        bastion = ec2.Instance(
            self, "Bastion06Jun2025",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=bastion_sg,
            key_name="PemKeyPair4ssh06-Jun-2025",  # Replace with your EC2 key pair name
        )

        # 5. RDS PostgreSQL in private subnet
        db = rds.DatabaseInstance(
            self, "psqldb06Jun2025",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_17_5
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[rds_sg],
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            allocated_storage=20,
            multi_az=False,
            publicly_accessible=False,
            removal_policy=RemovalPolicy.DESTROY,  # Allows cleanup with cdk destroy
            deletion_protection=False,
            credentials=rds.Credentials.from_generated_secret("postgres"),
            database_name="psqldb",
            backup_retention=None,
        )

        # 6. Output connection info
        CfnOutput(self, "BastionHostPublicIP", value=bastion.instance_public_ip)
        CfnOutput(self, "RDS_Endpoint", value=db.db_instance_endpoint_address)
        CfnOutput(self, "RDS_SecretName", value=db.secret.secret_name)
        # 4vl_JqWHTwU,_p4i2X59zpDitoDMvS