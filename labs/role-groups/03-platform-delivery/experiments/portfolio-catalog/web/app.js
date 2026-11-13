"use strict";

const labNames = {
  "01-network-fabric": "네트워크 패브릭",
  "02-cloud-foundation": "클라우드 인프라",
  "03-platform-delivery": "플랫폼 배포",
  "04-security-trust": "보안·접근 제어",
  "05-observability-sre": "관측·장애 분석",
  "06-change-automation": "변경 자동화",
  "07-recovery-dr": "백업·복구",
};
const statusNames = {
  LOCAL_VALIDATED: "로컬 검증",
  PREVIOUS_LOCAL_EVIDENCE: "기존 로컬 검증 기록",
  SOURCE_EXTRACTED_NOT_REVALIDATED: "이관 자료 · 재검증 전",
};
const query = document.querySelector("#query");
const labSelect = document.querySelector("#lab");
const statusSelect = document.querySelector("#status");
const catalog = document.querySelector("#catalog");
const result = document.querySelector("#result");
const groupTemplate = document.querySelector("#group-template");
const experimentTemplate = document.querySelector("#experiment-template");

function displayName(experiment) {
  return experiment.title ?? experiment.path.split("/").at(-1).replaceAll("-", " ");
}

function render(labs) {
  const search = query.value.trim().toLowerCase();
  const content = document.createDocumentFragment();
  let total = 0;
  let labCount = 0;

  for (const lab of labs) {
    if (labSelect.value && labSelect.value !== lab.id) continue;
    const name = labNames[lab.id] ?? lab.title;
    const experiments = lab.experiments.filter((experiment) => {
      const haystack = [name, lab.title, displayName(experiment), experiment.path].join(" ").toLowerCase();
      return haystack.includes(search) && (!statusSelect.value || statusSelect.value === experiment.status);
    });
    if (!experiments.length) continue;

    const group = groupTemplate.content.cloneNode(true);
    const heading = group.querySelector("h2 a");
    heading.textContent = name;
    heading.href = `/labs/role-groups/${lab.id}/README.md`;
    group.querySelector("header span").textContent = `${experiments.length}개`;
    const list = group.querySelector("ul");
    for (const experiment of experiments) {
      const item = experimentTemplate.content.cloneNode(true);
      const link = item.querySelector("a");
      link.textContent = displayName(experiment);
      link.href = `/${experiment.path}/README.md`;
      const status = item.querySelector("small");
      status.textContent = statusNames[experiment.status] ?? "상태 확인 필요";
      status.dataset.status = experiment.status;
      list.append(item);
    }
    total += experiments.length;
    labCount += 1;
    content.append(group);
  }
  catalog.replaceChildren(content);
  result.textContent = total ? `${labCount}개 랩 · 실험 ${total}개` : "검색 조건과 일치하는 실험이 없습니다.";
}

async function load() {
  try {
    const response = await fetch("/labs/role-groups/manifest.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { labs } = await response.json();
    for (const lab of labs) {
      labSelect.add(new Option(labNames[lab.id] ?? lab.title, lab.id));
    }
    document.querySelector(".filters").addEventListener("input", () => render(labs));
    render(labs);
  } catch {
    result.textContent = "카탈로그를 불러오지 못했습니다. 저장소 루트에서 로컬 서버를 실행한 뒤 페이지를 새로고침하세요.";
  }
}

document.querySelector(".filters").addEventListener("submit", (event) => event.preventDefault());
load();
