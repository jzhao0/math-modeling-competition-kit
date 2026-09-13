function matlab_audit
%MATLAB_AUDIT Inventory the Windows MATLAB environment for CUMCM 2026.
% Writes reports/matlab_environment.json under the repository root.

root = getenv('CUMCM_REPO_ROOT');
if strlength(root) == 0
    here = fileparts(mfilename('fullpath'));
    root = fileparts(here);
end
reportDir = fullfile(root, 'reports');
if ~exist(reportDir, 'dir')
    mkdir(reportDir);
end

info = struct();
info.timestamp = char(datetime('now', 'TimeZone', 'local', 'Format', "yyyy-MM-dd'T'HH:mm:ssXXX"));
info.matlab_version = version;
info.matlab_release = version('-release');
info.computer = computer;
info.arch = computer('arch');

products = ver;
installed = repmat(struct('name','','version','','release',''), numel(products), 1);
for k = 1:numel(products)
    installed(k).name = products(k).Name;
    installed(k).version = products(k).Version;
    installed(k).release = products(k).Release;
end
info.installed_products = installed;

checks = [ ...
    struct('label','Optimization Toolbox', 'product','Optimization Toolbox', 'feature','Optimization_Toolbox', 'probe','fmincon'), ...
    struct('label','Statistics and Machine Learning Toolbox', 'product','Statistics and Machine Learning Toolbox', 'feature','Statistics_Toolbox', 'probe','fitlm'), ...
    struct('label','Global Optimization Toolbox', 'product','Global Optimization Toolbox', 'feature','GADS_Toolbox', 'probe','ga'), ...
    struct('label','Curve Fitting Toolbox', 'product','Curve Fitting Toolbox', 'feature','Curve_Fitting_Toolbox', 'probe','fit'), ...
    struct('label','Symbolic Math Toolbox', 'product','Symbolic Math Toolbox', 'feature','Symbolic_Toolbox', 'probe','syms'), ...
    struct('label','Parallel Computing Toolbox', 'product','Parallel Computing Toolbox', 'feature','Distrib_Computing_Toolbox', 'probe','parpool') ...
];

results = repmat(struct('label','','installed',false,'license_test',false,'probe','','probe_found',false), numel(checks), 1);
productNames = string({products.Name});
for k = 1:numel(checks)
    results(k).label = checks(k).label;
    results(k).installed = any(strcmpi(productNames, checks(k).product));
    try
        results(k).license_test = logical(license('test', checks(k).feature));
    catch
        results(k).license_test = false;
    end
    results(k).probe = checks(k).probe;
    results(k).probe_found = exist(checks(k).probe, 'file') ~= 0 || exist(checks(k).probe, 'builtin') ~= 0;
end
info.priority_toolboxes = results;

% Base MATLAB sanity check: deterministic small linear solve.
A = [3 1; 1 2];
b = [9; 8];
x = A \ b;
info.base_smoke = struct('pass', norm(A*x-b) < 1e-10, 'solution', x(:)');

reportPath = fullfile(reportDir, 'matlab_environment.json');
fid = fopen(reportPath, 'w', 'n', 'UTF-8');
if fid < 0
    error('Could not open MATLAB audit report for writing: %s', reportPath);
end
cleanup = onCleanup(@() fclose(fid));
fwrite(fid, jsonencode(info, PrettyPrint=true), 'char');

fprintf('\nMATLAB R%s audit\n', info.matlab_release);
fprintf('Version: %s\n', info.matlab_version);
fprintf('Arch:    %s\n', info.arch);
fprintf('\nPriority toolbox audit:\n');
for k = 1:numel(results)
    fprintf('  %-40s installed=%-5s license=%-5s probe=%s\n', ...
        results(k).label, string(results(k).installed), string(results(k).license_test), string(results(k).probe_found));
end
fprintf('\nBase MATLAB smoke: %s\n', string(info.base_smoke.pass));
fprintf('Report: %s\n', reportPath);
end
