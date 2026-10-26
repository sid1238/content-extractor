// Sample resumes: 24 entries (3 per row x 8 rows).
const people = [
  ["Priya Sharma", "Senior Backend Engineer", ["Go", "PostgreSQL", "Kafka", "gRPC", "AWS"], "Stripe", "Razorpay", "B.Tech Computer Science, IIT Delhi"],
  ["Daniel Kim", "Frontend Engineer", ["React", "TypeScript", "GraphQL", "Jest", "CSS"], "Airbnb", "Squarespace", "B.S. Computer Science, UC Berkeley"],
  ["Maria Lopez", "Data Engineer", ["Spark", "Python", "Airflow", "Snowflake", "dbt"], "Netflix", "Lyft", "M.S. Data Science, Columbia University"],
  ["James Carter", "Full Stack Developer", ["Ruby on Rails", "React", "MySQL", "Redis", "Docker"], "Shopify", "Basecamp", "B.S. Software Engineering, University of Waterloo"],
  ["Aisha Bello", "Site Reliability Engineer", ["Kubernetes", "Terraform", "Prometheus", "Linux", "Go"], "Datadog", "DigitalOcean", "B.Eng. Computer Engineering, University of Lagos"],
  ["Lucas Martin", "Product Designer", ["Figma", "Prototyping", "User Research", "Design Systems", "Framer"], "Figma", "IDEO", "B.F.A. Interaction Design, RISD"],
  ["Wei Zhang", "Machine Learning Engineer", ["PyTorch", "Python", "CUDA", "Transformers", "MLOps"], "OpenAI", "Baidu Research", "M.S. Computer Science, Stanford University"],
  ["Emily Johnson", "Java Developer", ["Java", "Spring Boot", "Microservices", "AWS", "Kafka"], "Atlassian", "Capital One", "B.S. Computer Science, UT Austin"],
  ["Oliver Svensson", "iOS Engineer", ["Swift", "SwiftUI", "Combine", "Core Data", "XCTest"], "Spotify", "Klarna", "M.Sc. Software Engineering, KTH"],
  ["Rahul Verma", "Android Engineer", ["Kotlin", "Jetpack Compose", "RxJava", "Dagger", "Gradle"], "Uber", "Flipkart", "B.Tech Information Technology, NIT Trichy"],
  ["Sophie Turner", "Data Analyst", ["SQL", "Tableau", "Python", "Excel", "Looker"], "Snowflake", "Deloitte", "B.A. Economics, University of Michigan"],
  ["Hassan Ali", "Security Engineer", ["Network Security", "Rust", "Threat Modeling", "SIEM", "Pen Testing"], "Cloudflare", "CrowdStrike", "M.Sc. Cyber Security, Imperial College London"],
  ["Grace Chen", "Cloud Solutions Architect", ["Azure", "C#", ".NET", "Kubernetes", "Solution Design"], "Microsoft", "Accenture", "B.S. Computer Engineering, University of Washington"],
  ["Noah Williams", "Software Engineer, Growth", ["TypeScript", "Node.js", "A/B Testing", "SQL", "Segment"], "Notion", "Dropbox", "B.S. Mathematics, NYU"],
  ["Fatima Khan", "Product Manager", ["Roadmapping", "Agile", "Analytics", "SQL", "Stakeholder Mgmt"], "Salesforce", "Zendesk", "MBA, Kellogg School of Management"],
  ["Ethan Brooks", "QA Automation Engineer", ["Selenium", "Cypress", "JavaScript", "Jenkins", "Postman"], "Adobe", "Intuit", "B.S. Information Systems, San Jose State"],
  ["Ananya Iyer", "Embedded Software Engineer", ["C++", "RTOS", "Embedded Linux", "ARM", "Python"], "NVIDIA", "Qualcomm", "M.S. Electrical Engineering, Georgia Tech"],
  ["Marcus Reed", "Blockchain Engineer", ["Solidity", "Ethereum", "Go", "Cryptography", "Hardhat"], "Coinbase", "ConsenSys", "B.S. Computer Science, Purdue University"],
  ["Isabella Rossi", "DevOps Engineer", ["GitHub Actions", "Docker", "Azure", "Bash", "Ansible"], "GitHub", "Red Hat", "B.Sc. Informatics, Politecnico di Milano"],
  ["Kevin Nguyen", "Junior Software Engineer", ["Python", "JavaScript", "Git", "REST APIs", "React"], "Duolingo (Intern)", "CMU Robotics Lab", "B.S. Computer Science, Carnegie Mellon University"],
  ["Laura Schmidt", "Research Scientist, NLP", ["NLP", "PyTorch", "Statistics", "LLMs", "JAX"], "Meta AI", "DeepMind (Intern)", "Ph.D. Computer Science, ETH Zurich"],
  ["Chloe Wilson", "UX Writer", ["UX Writing", "Content Strategy", "Figma", "Localization", "A/B Testing"], "Canva", "Atlassian", "B.A. English & Media, University of Sydney"],
  ["Diego Fernandez", "Solutions Engineer", ["Spark", "Scala", "Delta Lake", "Python", "Presales"], "Databricks", "Cloudera", "B.S. Computer Science, University of Colorado"],
  ["Samuel Okafor", "Engineering Manager", ["People Leadership", "System Design", "Python", "Hiring", "OKRs"], "Tesla", "Amazon", "M.S. Computer Science, Texas A&M"],
];

const resumes = people.map(([name, title, skills, current, previous, education], i) => {
  const years = 2 + (i % 7);
  const slug = name.toLowerCase().replace(/[^a-z]+/g, ".");
  return {
    id: i + 1,
    name,
    title,
    email: `${slug}@example.com`,
    phone: `(555) 01${String(i).padStart(2, "0")}-${String(4000 + i * 37).slice(-4)}`,
    location: ["San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Remote", "London, UK"][i % 6],
    years,
    summary: `${title} with ${years}+ years of experience building reliable, user-focused products. Strong in ${skills.slice(0, 3).join(", ")}, with a track record of shipping high-impact work in collaborative, fast-moving teams.`,
    skills,
    experience: [
      {
        company: current,
        role: title,
        period: `${2026 - Math.ceil(years / 2)} – Present`,
        bullets: [
          `Led delivery of a core initiative using ${skills[0]} and ${skills[1]}, improving key metrics by ${15 + i}%.`,
          `Partnered with product and design to scope, plan and ship quarterly roadmap items.`,
          `Mentored ${1 + (i % 4)} teammates and drove adoption of ${skills[2]} best practices.`,
        ],
      },
      {
        company: previous,
        role: title.replace(/^Senior |^Junior /, ""),
        period: `${2026 - years} – ${2026 - Math.ceil(years / 2)}`,
        bullets: [
          `Built and maintained features with ${skills[3]}, used by thousands of customers.`,
          `Reduced turnaround time by ${20 + (i % 5) * 5}% by automating manual workflows.`,
        ],
      },
    ],
    education,
  };
});

export default resumes;
