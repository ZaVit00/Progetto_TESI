// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract BatchVerifier {
    struct BatchInfo {
        string merkleRoot;
        string cidIpfs;
    }

    mapping(uint256 => BatchInfo) public batches;

    /// @notice Salva o sovrascrive un batch con il relativo merkleRoot e cidIpfs.
    /// @dev Se esiste già un batch con lo stesso id, viene sovrascritto.
    /// da utilizzare in caso di test per sovrascrivere batch esistenti (SOLO IN CASO DI TEST)
    function salvaBatch(uint256 id, string memory merkleRoot, string memory cidIpfs) public {
        batches[id] = BatchInfo(merkleRoot, cidIpfs);

    }

    /// @notice Restituisce i dati associati a un batch
    function getBatch(uint256 id) public view returns (string memory, string memory) {
        BatchInfo memory info = batches[id];
        return (info.merkleRoot, info.cidIpfs);
    }
}
