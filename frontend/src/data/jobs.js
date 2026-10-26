// Sample job listings: 24 entries (3 per row x 8 rows).
const jobs = [
  { id: 1, company: "Stripe", role: "Senior Backend Engineer", location: "Remote", experience: "5+ years", skills: ["Go", "PostgreSQL", "Distributed Systems", "gRPC"] },
  { id: 2, company: "Airbnb", role: "Frontend Engineer", location: "San Francisco, CA", experience: "3+ years", skills: ["React", "TypeScript", "GraphQL", "CSS"] },
  { id: 3, company: "Netflix", role: "Data Engineer", location: "Los Gatos, CA", experience: "4+ years", skills: ["Spark", "Python", "Kafka", "AWS"] },
  { id: 4, company: "Shopify", role: "Full Stack Developer", location: "Remote", experience: "2+ years", skills: ["Ruby on Rails", "React", "MySQL", "Redis"] },
  { id: 5, company: "Datadog", role: "Site Reliability Engineer", location: "New York, NY", experience: "4+ years", skills: ["Kubernetes", "Terraform", "Linux", "Prometheus"] },
  { id: 6, company: "Figma", role: "Product Designer", location: "San Francisco, CA", experience: "3+ years", skills: ["Figma", "Prototyping", "User Research", "Design Systems"] },
  { id: 7, company: "OpenAI", role: "Machine Learning Engineer", location: "San Francisco, CA", experience: "5+ years", skills: ["PyTorch", "Python", "CUDA", "Transformers"] },
  { id: 8, company: "Atlassian", role: "Java Developer", location: "Austin, TX", experience: "3+ years", skills: ["Java", "Spring Boot", "Microservices", "AWS"] },
  { id: 9, company: "Spotify", role: "iOS Engineer", location: "Stockholm, SE", experience: "3+ years", skills: ["Swift", "SwiftUI", "Combine", "Xcode"] },
  { id: 10, company: "Uber", role: "Android Engineer", location: "Seattle, WA", experience: "4+ years", skills: ["Kotlin", "Jetpack Compose", "RxJava", "Gradle"] },
  { id: 11, company: "Snowflake", role: "Data Analyst", location: "Remote", experience: "1+ years", skills: ["SQL", "Tableau", "Python", "dbt"] },
  { id: 12, company: "Cloudflare", role: "Security Engineer", location: "London, UK", experience: "5+ years", skills: ["Network Security", "Rust", "Threat Modeling", "Zero Trust"] },
  { id: 13, company: "Microsoft", role: "Cloud Solutions Architect", location: "Redmond, WA", experience: "7+ years", skills: ["Azure", "C#", ".NET", "Solution Design"] },
  { id: 14, company: "Notion", role: "Software Engineer, Growth", location: "New York, NY", experience: "2+ years", skills: ["TypeScript", "Node.js", "A/B Testing", "SQL"] },
  { id: 15, company: "Salesforce", role: "Product Manager", location: "Chicago, IL", experience: "5+ years", skills: ["Roadmapping", "Agile", "Analytics", "Stakeholder Mgmt"] },
  { id: 16, company: "Adobe", role: "QA Automation Engineer", location: "San Jose, CA", experience: "2+ years", skills: ["Selenium", "Cypress", "JavaScript", "CI/CD"] },
  { id: 17, company: "NVIDIA", role: "Embedded Software Engineer", location: "Santa Clara, CA", experience: "4+ years", skills: ["C++", "RTOS", "Embedded Linux", "ARM"] },
  { id: 18, company: "Coinbase", role: "Blockchain Engineer", location: "Remote", experience: "3+ years", skills: ["Solidity", "Ethereum", "Go", "Cryptography"] },
  { id: 19, company: "GitHub", role: "DevOps Engineer", location: "Remote", experience: "3+ years", skills: ["GitHub Actions", "Docker", "Azure", "Bash"] },
  { id: 20, company: "Duolingo", role: "Junior Software Engineer", location: "Pittsburgh, PA", experience: "0-1 years", skills: ["Python", "JavaScript", "Git", "REST APIs"] },
  { id: 21, company: "Meta", role: "Research Scientist, NLP", location: "Menlo Park, CA", experience: "PhD + 2 years", skills: ["NLP", "PyTorch", "Statistics", "LLMs"] },
  { id: 22, company: "Canva", role: "UX Writer", location: "Sydney, AU", experience: "2+ years", skills: ["UX Writing", "Content Strategy", "Figma", "Localization"] },
  { id: 23, company: "Databricks", role: "Solutions Engineer", location: "Denver, CO", experience: "4+ years", skills: ["Spark", "Scala", "Delta Lake", "Customer Facing"] },
  { id: 24, company: "Tesla", role: "Engineering Manager", location: "Austin, TX", experience: "8+ years", skills: ["People Leadership", "System Design", "Python", "Hiring"] },
];

export default jobs;
